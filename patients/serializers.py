from rest_framework import serializers
from .models import Patient
from accounts.models import User


class UserSerializer(serializers.ModelSerializer):
    """Serializer cho user, bao gồm cả các thông tin cá nhân"""
    class Meta:
        model = User
        fields = [
            'username', 'email', 'first_name', 'last_name', 
            'phone', 'avatar', 'role', 'date_joined', 'is_active',
            'birthday', 'gender', 'address', 'cccd', 'ethinic_group'
        ]
        read_only_fields = ['username', 'role', 'date_joined', 'is_active']


class PatientSerializer(serializers.ModelSerializer):
    """Serializer chính cho bệnh nhân, có nested user"""
    user = UserSerializer()

    class Meta:
        model = Patient
        fields = [
            'id',
            'user',
            'health_insurance_number',
            'occupation',
            'medical_history',
        ]
        read_only_fields = ['id']

    def update(self, instance, validated_data):
        """
        Ghi đè update() để cho phép cập nhật cả thông tin trong bảng User
        """
        user_data = validated_data.pop('user', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if user_data:
            user = instance.user
            for attr, value in user_data.items():
                setattr(user, attr, value)
            user.save()

        return instance