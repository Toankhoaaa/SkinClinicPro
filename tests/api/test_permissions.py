import pytest
from django.urls import reverse
from rest_framework import status
from tests.factories.user_factory import PatientFactory, DoctorFactory

@pytest.mark.django_db
class TestPatientPermissions:
    
    def test_patient_can_access_own_profile(self, api_client):
        """
        CASE 1: Happy Path
        Bệnh nhân có thể xem hồ sơ của chính mình qua endpoint 'me'.
        """
        patient = PatientFactory()
        api_client.force_authenticate(user=patient.user)
        
        url = reverse('patient-me') # Endpoint: /api/patients/me/
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['data']['user']['username'] == patient.user.username

    def test_patient_cannot_list_all_patients(self, api_client):
        """
        CASE 2: Negative Test (List)
        Bệnh nhân thường KHÔNG được xem danh sách tất cả bệnh nhân (Quyền này chỉ của Admin).
        """
        patient = PatientFactory()
        api_client.force_authenticate(user=patient.user)
        
        url = reverse('patient-list') # Endpoint: /api/patients/
        response = api_client.get(url)
        
        # Mong đợi: 403 Forbidden
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_patient_cannot_access_other_profile_by_id(self, api_client):
        """
        CASE 3: Negative Test (IDOR - Insecure Direct Object Reference)
        Bệnh nhân A cố tình đổi ID trên URL để xem hồ sơ của Bệnh nhân B.
        """
        patient_a = PatientFactory()
        patient_b = PatientFactory()
        
        # Login user A
        api_client.force_authenticate(user=patient_a.user)
        
        # Cố truy cập URL của B: /api/patients/{id_của_B}/
        url = reverse('patient-detail', kwargs={'pk': patient_b.id})
        response = api_client.get(url)
        
        # Mong đợi: 403 Forbidden (Hoặc 404 tùy logic get_queryset)
        # Với logic IsAdminUser ở view detail, nó sẽ trả về 403
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_patient_cannot_update_other_profile(self, api_client):
        """
        CASE 4: Negative Test (Update)
        Bệnh nhân A cố gắng sửa thông tin (PUT/PATCH) của Bệnh nhân B.
        """
        patient_a = PatientFactory()
        patient_b = PatientFactory()
        
        api_client.force_authenticate(user=patient_a.user)
        
        url = reverse('patient-detail', kwargs={'pk': patient_b.id})
        payload = {"occupation": "Hacker"}
        
        response = api_client.patch(url, payload)
        
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_unauthenticated_user_cannot_access_profile(self, api_client):
        """
        CASE 5: Security Test
        Người dùng chưa đăng nhập (Anonymous) không thể truy cập API.
        """
        url = reverse('patient-me')
        response = api_client.get(url)
        
        # Mong đợi: 401 Unauthorized
        assert response.status_code == status.HTTP_401_UNAUTHORIZED