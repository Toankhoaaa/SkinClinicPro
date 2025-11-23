from rest_framework import serializers
from django.contrib.auth import get_user_model, authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.db import transaction  # <<< Import Transaction

from accounts.models import Role
from patients.models import Patient  # <<< Import Patient
from doctor.models import Doctor     # <<< Import Doctor

User = get_user_model()


class RoleSerializer(serializers.ModelSerializer):
    """
    (Không thay đổi) - Serializer này đã tốt.
    """
    class Meta:
        model = Role
        fields = ['id', 'name']


class UserRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True, 
        required=True, 
        validators=[validate_password]
    )
    password_confirm = serializers.CharField(write_only=True, required=True)
    role = serializers.PrimaryKeyRelatedField(queryset=Role.objects.all())

    class Meta:
        model = User
        fields = (
            'username', 'email', 'phone', 'gender', 'avatar'
            'password', 'password_confirm', 
            'role', 'first_name', 'last_name'
        )
        extra_kwargs = {
            'password': {'write_only': True},
            'username': {'required': True},
        }

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({"password_confirm": "Mật khẩu xác nhận không khớp."})
        
        if User.objects.filter(username=attrs['username']).exists():
            raise serializers.ValidationError({"username": "Tên đăng nhập đã tồn tại."})
        
        if User.objects.filter(email=attrs['email']).exists():
            raise serializers.ValidationError({"email": "Email đã tồn tại."})
            
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        """
        Ghi đè hàm create để tự động tạo Patient/Doctor profile
        """
        role_obj = validated_data.pop('role')
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        
        # 2. Tạo User
        user = User.objects.create_user(
            **validated_data, # Gồm username, email, phone, first_name...
            role=role_obj
        )
        # set_password sẽ hash mật khẩu
        user.set_password(password) 
        user.save()

        # 3. TỰ ĐỘNG TẠO PROFILE (Quan trọng nhất)
        try:
            role_name = role_obj.name.lower()
            
            print(f"DEBUG: Đang tạo profile. Role name nhận được là: '{role_name}'")
            if role_name == 'patient':
                Patient.objects.create(user=user)
            elif role_name == 'doctor':
                # Tạo profile Doctor "chờ", giá 0
                Doctor.objects.create(user=user, price=0) 
                
        except Exception as e:
            # Nếu tạo profile (Patient/Doctor) lỗi
            # thì hủy luôn việc tạo User (nhờ @transaction.atomic)
            raise serializers.ValidationError(f"Lỗi khi tạo profile: {str(e)}")
        
        return user


class UserLoginSerializer(serializers.Serializer):
    """
    Cho phép login bằng cả username và email rất tiện.
    """
    username = serializers.CharField(label="Tên đăng nhập hoặc Email")
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        username_or_email = attrs.get('username')
        password = attrs.get('password')

        if not username_or_email or not password:
            raise serializers.ValidationError("Vui lòng nhập tên đăng nhập/email và mật khẩu.")

        # Thử authenticate bằng username
        user = authenticate(username=username_or_email, password=password)

        if not user:
            # Nếu thất bại, thử tìm user bằng email
            try:
                user_obj = User.objects.get(email=username_or_email)
                # Authenticate lại bằng username thật của user đó
                user = authenticate(username=user_obj.username, password=password)
            except User.DoesNotExist:
                pass # Sẽ đi tới raise lỗi ở dưới

        if not user:
            raise serializers.ValidationError("Tên đăng nhập, email hoặc mật khẩu không đúng.")

        if not user.is_active:
            raise serializers.ValidationError("Tài khoản của bạn đã bị vô hiệu hóa.")

        attrs['user'] = user
        return attrs


class PasswordResetSerializer(serializers.Serializer):
    token = serializers.CharField(label="Recovery Token")
    new_password = serializers.CharField(
        write_only=True, 
        required=True,
        validators=[validate_password] # Dùng validator
    )
    new_password_confirm = serializers.CharField(write_only=True, required=True)

    def validate_token(self, value):
        """
        Kiểm tra token có tồn tại trong trường 'recovery_token' không
        """
        try:
            # Sửa 'reset_token' thành 'recovery_token' cho đúng model
            user = User.objects.get(recovery_token=value) 
        except User.DoesNotExist:
            raise serializers.ValidationError("Token không hợp lệ hoặc đã hết hạn.")
        
        self.context['user'] = user # Lưu user vào context để dùng trong hàm save
        return value

    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError({"new_password_confirm": "Mật khẩu xác nhận không khớp."})
        return attrs
        
    def save(self):
        """
        Thực thi việc đổi mật khẩu
        """
        user = self.context['user']
        new_password = self.validated_data['new_password']
        
        user.set_password(new_password)
        user.recovery_token = None # Xóa token sau khi đã dùng
        user.save()
        return user