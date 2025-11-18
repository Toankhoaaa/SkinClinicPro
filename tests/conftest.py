import pytest
from rest_framework.test import APIClient
from tests.factories.user_factory import UserFactory, DoctorFactory, PatientFactory

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def auto_login_user(api_client, user_factory):
    """Fixture tạo user và login sẵn, trả về client đã có token"""
    user = user_factory()
    api_client.force_authenticate(user=user)
    return api_client, user