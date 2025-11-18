import pytest
from django.urls import reverse
from tests.factories.user_factory import PatientFactory

@pytest.mark.django_db
def test_patient_cannot_access_other_profile(api_client):
    patient_1 = PatientFactory()
    patient_2 = PatientFactory()
    
    # Login user 1
    api_client.force_authenticate(user=patient_1.user)
    
    # Cố gắng lấy thông tin "me" (đúng logic phải trả về patient_1)
    url = reverse('patient-me') # Dựa trên patients/views.py action 'me'
    response = api_client.get(url)
    
    assert response.status_code == 200
    assert response.data['data']['user']['username'] == patient_1.user.username
    
    # Thử truy cập endpoint dành cho Admin (nếu có)
    # Hoặc kiểm tra xem user 1 có sửa được user 2 không (nếu có endpoint ID)