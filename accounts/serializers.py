from rest_framework import serializers
from django.contrib.auth import get_user_model, authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from accounts.models import Role

User = get_user_model()


class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = ['id', 'name']


class UserSignupSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)
    role = serializers.PrimaryKeyRelatedField(queryset=Role.objects.all())

    class Meta:
        model = User
        fields = ('username', 'password', 'password_confirm', 'role', 'first_name', 'last_name')
        extra_kwargs = {
            'password': {'write_only': True},
        }

    def validate_password(self, value):
        try:
            validate_password(value)
        except ValidationError as e:
            raise serializers.ValidationError(e.messages)
        return value

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({"password_confirm": "Mật khẩu xác nhận không khớp."})
        elif User.objects.filter(username=attrs['username']).exists():
            raise serializers.ValidationError({"username": "Tên đăng nhập đã tồn tại."})
        return attrs

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        user = User.objects.create_user(**validated_data)
        user.set_password(password)
        user.save()
        return user


class UserLoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')

        if not username or not password:
            raise serializers.ValidationError("Vui lòng nhập tên đăng nhập và mật khẩu.")

        user = authenticate(username=username, password=password)
        if not user:
            # Cho phép đăng nhập bằng email
            try:
                user_obj = User.objects.get(email=username)
                user = authenticate(username=user_obj.username, password=password)
            except User.DoesNotExist:
                raise serializers.ValidationError("Tên đăng nhập hoặc mật khẩu không đúng.")

        if not user.is_active:
            raise serializers.ValidationError("Tài khoản của bạn đã bị vô hiệu hóa.")

        attrs['user'] = user
        return attrs


class ResetTokenSerializer(serializers.Serializer):
    token = serializers.CharField()
    new_password = serializers.CharField(write_only=True)

    def validate_token(self, value):
        try:
            User.objects.get(reset_token=value)
        except User.DoesNotExist:
            raise serializers.ValidationError("Token không hợp lệ.")
        return value
