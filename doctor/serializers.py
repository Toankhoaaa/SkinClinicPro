from rest_framework import serializers
from .models import Doctor
from accounts.models import User


class  UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'phone', 'avatar', 'role', 'date_joined', 'is_active']
        read_only_fields = ['username', 'role', 'date_joined', 'is_active']

class DoctorSerializer(serializers.ModelSerializer):
    user = UserSerializer()

    class Meta:
        model = Doctor
        fields = [
            'id',
            'user',
            'specialty',
            'room',
            'price',
            'experience',
            'credentiaUrl',
            'verificationStatus',
            'is_available',
            'created_at',
            'description',
        ]
        read_only_fields = ['id', 'user', 'is_available', 'created_at']

    def update(self, instance, validated_data):
        """
        Ghi đè update() để cho phép cập nhật cả thông tin trong bảng User
        """
        user_data = validated_data.pop('user', None)

        # Cập nhật thông tin Patient
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if user_data:
            user = instance.user
            for attr, value in user_data.items():
                setattr(user, attr, value)
            user.save()

        return instance