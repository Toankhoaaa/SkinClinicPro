import pytest
from django.urls import reverse
from rest_framework import status
from tests.factories.user_factory import UserFactory

@pytest.mark.django_db
class TestAuthentication:
    
    # --- HAPPY PATHS (Thành công) ---

    def test_user_registration_success(self, api_client):
        """Test đăng ký tài khoản mới thành công"""
        url = reverse('signup')
        
        # Tạo Role trước khi test
        from accounts.models import Role
        role_patient, _ = Role.objects.get_or_create(id=3, name="Patient")
        
        payload = {
            "username": "newuser",
            "password": "Strong@Pass123!", 
            "password_confirm": "Strong@Pass123!",
            "email": "new@example.com",
            "first_name": "Nguyen",
            "last_name": "Van A",
            "role": role_patient.id
        }
        
        response = api_client.post(url, payload)
        assert response.status_code == status.HTTP_201_CREATED
        assert 'tokens' in response.data

    def test_user_login_success(self, api_client):
        """Test đăng nhập và nhận token thành công"""
        user = UserFactory(username="existinguser", email="test@example.com")
        # Set mật khẩu cứng để test login
        user.set_password("Strong@Pass123!")
        user.save()
        
        url = reverse('login')
        payload = {
            "username": "existinguser",
            "password": "Strong@Pass123!" 
        }
        
        response = api_client.post(url, payload)
        assert response.status_code == status.HTTP_200_OK
        assert 'access' in response.data['tokens']

    # --- NEGATIVE CASES (Các trường hợp lỗi) ---

    def test_login_wrong_password(self, api_client):
        """Test đăng nhập sai mật khẩu"""
        user = UserFactory(username="wrongpassuser")
        user.set_password("Strong@Pass123!")
        user.save()
        
        url = reverse('login')
        payload = {
            "username": "wrongpassuser",
            "password": "WrongPassword"
        }
        response = api_client.post(url, payload)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_register_weak_password(self, api_client):
        """
        Test đăng ký với mật khẩu quá yếu (ví dụ: quá ngắn, toàn số).
        Django Validator sẽ chặn trường hợp này.
        """
        url = reverse('signup')
        from accounts.models import Role
        role, _ = Role.objects.get_or_create(id=3, name="Patient")

        payload = {
            "username": "weak_user",
            "password": "123",       # Quá ngắn
            "password_confirm": "123",
            "email": "weak@test.com",
            "role": role.id
        }
        
        response = api_client.post(url, payload)
        
        # Kỳ vọng: 400 Bad Request
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        # Kiểm tra xem lỗi có liên quan đến password không
        # (Lỗi thường nằm trong dict errors)
        errors = str(response.data).lower()
        assert "password" in errors or "mật khẩu" in errors

    def test_register_invalid_email(self, api_client):
        """Test đăng ký với định dạng email sai"""
        url = reverse('signup')
        from accounts.models import Role
        role, _ = Role.objects.get_or_create(id=3, name="Patient")

        payload = {
            "username": "invalid_email_user",
            "password": "Strong@Pass123!",
            "password_confirm": "Strong@Pass123!",
            "email": "not-an-email",
            "role": role.id
        }
        
        response = api_client.post(url, payload)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        
        # FIX: Kiểm tra linh hoạt vị trí của key 'email'
        if 'errors' in response.data:
            assert "email" in response.data['errors']
        else:
            assert "email" in response.data

    def test_register_password_mismatch(self, api_client):
        """Test mật khẩu xác nhận không khớp"""
        url = reverse('signup')
        from accounts.models import Role
        role, _ = Role.objects.get_or_create(id=3, name="Patient")

        payload = {
            "username": "mismatch_user",
            "password": "Strong@Pass123!",
            "password_confirm": "KhongGiong!", # Khác nhau
            "email": "mismatch@test.com",
            "role": role.id
        }
        
        response = api_client.post(url, payload)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        # Kiểm tra message lỗi
        if 'password_confirm' in response.data:
            pass # Đúng kỳ vọng DRF
        elif 'errors' in response.data:
            assert 'password_confirm' in response.data['errors']