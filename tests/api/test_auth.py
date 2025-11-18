import pytest
from django.urls import reverse
from rest_framework import status
from tests.factories.user_factory import UserFactory

@pytest.mark.django_db
class TestAuthentication:
    
    def test_user_registration_success(self, api_client):
        """Test đăng ký tài khoản mới thành công"""
        url = reverse('signup')  # Dựa trên accounts/urls.py
        payload = {
            "username": "newuser",
            "password": "strongpassword123",
            "password_confirm": "strongpassword123",
            "email": "new@example.com",
            "first_name": "Nguyen",
            "last_name": "Van A",
            "role": 3  # Giả sử ID 3 là Patient (cần khớp với DB của bạn hoặc dùng Factory)
        }
        
        # Lưu ý: Bạn cần đảm bảo Role ID 3 tồn tại. 
        # Tốt nhất là tạo Role trong setUp hoặc dùng fixture nếu Role table trống.
        from accounts.models import Role
        if not Role.objects.filter(id=3).exists():
             Role.objects.create(id=3, name="Patient")

        response = api_client.post(url, payload)
        assert response.status_code == status.HTTP_201_CREATED
        assert 'tokens' in response.data
        assert 'access' in response.data['tokens']

    def test_user_login_success(self, api_client):
        """Test đăng nhập và nhận token"""
        # Given: User đã tồn tại (password mặc định trong factory là 'password123')
        user = UserFactory(username="existinguser", email="test@example.com")
        
        url = reverse('login')
        payload = {
            "username": "existinguser",
            "password": "password123" 
        }
        
        # When
        response = api_client.post(url, payload)
        
        # Then
        assert response.status_code == status.HTTP_200_OK
        assert 'access' in response.data['tokens']

    def test_login_wrong_password(self, api_client):
        """Test đăng nhập sai pass bị chặn"""
        user = UserFactory(username="wrongpassuser")
        url = reverse('login')
        payload = {
            "username": "wrongpassuser",
            "password": "wrongpassword"
        }
        response = api_client.post(url, payload)
        assert response.status_code == status.HTTP_400_BAD_REQUEST