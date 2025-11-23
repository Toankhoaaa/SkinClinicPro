import pytest
from django.urls import reverse
from rest_framework import status
from tests.factories.user_factory import DoctorFactory, PatientFactory
from specialities.models import Speciality

@pytest.mark.django_db
class TestDoctorSearchAndFilter:
    
    def test_list_doctors_returns_only_verified_and_available(self, api_client):
        """
        Test Case chuẩn (Happy Path): 
        Chỉ trả về bác sĩ đã xác minh (VERIFIED) và có sẵn (is_available=True).
        """
        # 1. Tạo bác sĩ hợp lệ
        valid_doctor = DoctorFactory(verificationStatus="VERIFIED", is_available=True)
        
        # 2. Login
        patient = PatientFactory()
        api_client.force_authenticate(user=patient.user)
        
        # 3. Gọi API
        url = reverse('doctor-list')
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        # Kiểm tra bác sĩ hợp lệ có trong danh sách
        doctor_ids = [d['id'] for d in response.data]
        assert valid_doctor.id in doctor_ids

    def test_list_excludes_unverified_doctors(self, api_client):
        """
        Test Case Sai (Negative): 
        Bác sĩ chưa xác minh (PENDING/REJECTED) KHÔNG ĐƯỢC xuất hiện.
        """
        # 1. Tạo bác sĩ PENDING và REJECTED
        pending_doctor = DoctorFactory(verificationStatus="PENDING")
        rejected_doctor = DoctorFactory(verificationStatus="REJECTED")
        
        # 2. Login & Gọi API
        patient = PatientFactory()
        api_client.force_authenticate(user=patient.user)
        
        response = api_client.get(reverse('doctor-list'))
        
        # 3. Verify: ID của họ không được phép có trong response
        doctor_ids = [d['id'] for d in response.data]
        assert pending_doctor.id not in doctor_ids
        assert rejected_doctor.id not in doctor_ids

    def test_list_excludes_unavailable_doctors(self, api_client):
        """
        Test Case Sai (Negative): 
        Bác sĩ đang bận/tắt hoạt động (is_available=False) KHÔNG ĐƯỢC xuất hiện.
        """
        # 1. Tạo bác sĩ không rảnh
        busy_doctor = DoctorFactory(is_available=False, verificationStatus="VERIFIED")
        
        # 2. Login & Gọi API
        patient = PatientFactory()
        api_client.force_authenticate(user=patient.user)
        
        response = api_client.get(reverse('doctor-list'))
        
        # 3. Verify
        doctor_ids = [d['id'] for d in response.data]
        assert busy_doctor.id not in doctor_ids

    def test_filter_doctor_by_non_existent_speciality(self, api_client):
        """Test Case Sai (Edge Case)"""
        spec_a = Speciality.objects.create(name="Khoa A")
        DoctorFactory(specialty=spec_a)
        spec_b = Speciality.objects.create(name="Khoa B (Rỗng)")
        
        patient = PatientFactory()
        api_client.force_authenticate(user=patient.user)
        
        url = reverse('doctor-list') + f'?specialty={spec_b.id}'
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        
        # FIX: Sửa logic check ID
        if len(response.data) > 0:
            # specialty trả về ID (int), không phải dict
            specialty_ids = [d['specialty'] for d in response.data if d['specialty']]
            assert spec_a.id not in specialty_ids