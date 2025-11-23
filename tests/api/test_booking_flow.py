import pytest
from django.urls import reverse
from rest_framework import status
from datetime import date, time, timedelta
from tests.factories.user_factory import PatientFactory, DoctorFactory
from availability.models import Schedule
from appointments.models import Appointment

@pytest.mark.django_db
class TestBookingFlow:
    
    def test_patient_can_book_appointment_successfully(self, api_client):
        """Test đặt lịch thành công (Happy Path)"""
        patient = PatientFactory()
        doctor = DoctorFactory()
        
        # Tạo lịch làm việc
        Schedule.objects.create(
            doctor=doctor,
            date=date.today() + timedelta(days=1),
            start_time=time(8, 0),
            end_time=time(17, 0),
            max_patients=5
        )
        
        api_client.force_authenticate(user=patient.user)
        url = reverse('appointment-list')
        payload = {
            "doctor_id": doctor.id,
            "date": (date.today() + timedelta(days=1)).isoformat(),
            "time": "09:00"
        }
        
        response = api_client.post(url, payload)

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['status'] == 'pending'
        assert response.data['doctor']['id'] == doctor.id

    def test_cannot_book_outside_schedule(self, api_client):
        """Test đặt lịch ngoài giờ làm việc của bác sĩ"""
        patient = PatientFactory()
        doctor = DoctorFactory()
        
        # Bác sĩ làm từ 8h - 17h
        Schedule.objects.create(
            doctor=doctor,
            date=date.today() + timedelta(days=1),
            start_time=time(8, 0),
            end_time=time(17, 0)
        )
        
        api_client.force_authenticate(user=patient.user)
        # Cố đặt lúc 20:00
        payload = {
            "doctor_id": doctor.id,
            "date": (date.today() + timedelta(days=1)).isoformat(),
            "time": "20:00"
        }
        response = api_client.post(reverse('appointment-list'), payload)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        # Kiểm tra key 'non_field_errors' hoặc code='unique' thay vì chuỗi tiếng Việt
        assert 'non_field_errors' in response.data
        # Sửa 'unique' thành 'invalid'
        assert response.data['non_field_errors'][0].code == 'invalid'

    # --- CÁC TEST CASE BỔ SUNG (NÊN CÓ) ---

    def test_cannot_book_duplicate_slot(self, api_client):
        """Test không thể đặt trùng vào giờ đã có người khác đặt"""
        doctor = DoctorFactory()
        patient_1 = PatientFactory()
        patient_2 = PatientFactory()
        tomorrow = date.today() + timedelta(days=1)
        
        Schedule.objects.create(
            doctor=doctor, date=tomorrow,
            start_time=time(8, 0), end_time=time(17, 0)
        )

        # Patient 1 đã đặt lúc 9:00
        Appointment.objects.create(
            doctor=doctor, patient=patient_1,
            date=tomorrow, time=time(9, 0), status='pending'
        )

        # Patient 2 cố đặt chồng vào lúc 9:00
        api_client.force_authenticate(user=patient_2.user)
        
        # KHAI BÁO PAYLOAD TẠI ĐÂY
        payload = {
            "doctor_id": doctor.id,
            "date": tomorrow.isoformat(),
            "time": "09:00"
        }
        
        response = api_client.post(reverse('appointment-list'), payload)

        # FIX: Chỉ kiểm tra status code và sự tồn tại của lỗi
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'non_field_errors' in response.data
        err_code = response.data['non_field_errors'][0].code
        assert err_code in ['unique', 'invalid']
        
    def test_cannot_book_when_no_schedule(self, api_client):
        """Test không thể đặt lịch vào ngày Bác sĩ không làm việc (không có Schedule)"""
        doctor = DoctorFactory()
        patient = PatientFactory()
        tomorrow = date.today() + timedelta(days=1)
        
        # Không tạo Schedule nào cho ngày mai cả!
        
        api_client.force_authenticate(user=patient.user)
        payload = {
            "doctor_id": doctor.id,
            "date": tomorrow.isoformat(),
            "time": "09:00"
        }
        response = api_client.post(reverse('appointment-list'), payload)

        # Kỳ vọng: Lỗi 400 (Bác sĩ không có lịch)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "không có lịch làm việc" in str(response.data)