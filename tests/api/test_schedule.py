import pytest
from django.urls import reverse
from rest_framework import status
from datetime import date, time, timedelta
from tests.factories.user_factory import DoctorFactory, PatientFactory
from availability.models import Schedule

@pytest.mark.django_db
class TestScheduleManagement:
    
    # --- HAPPY PATHS (Các trường hợp thành công) ---

    def test_doctor_create_schedule_success(self, api_client):
        """Bác sĩ tạo lịch làm việc hợp lệ"""
        doctor = DoctorFactory()
        api_client.force_authenticate(user=doctor.user)
        
        url = reverse('schedule-list') # Dựa trên availability/urls.py router
        tomorrow = date.today() + timedelta(days=1)
        payload = {
            "date": tomorrow.isoformat(),
            "start_time": "08:00",
            "end_time": "12:00",
            "max_patients": 10
        }
        
        response = api_client.post(url, payload)
        
        assert response.status_code == status.HTTP_201_CREATED
        assert Schedule.objects.count() == 1
        assert Schedule.objects.first().doctor == doctor

    def test_doctor_update_schedule(self, api_client):
        """Bác sĩ có thể chỉnh sửa lịch làm việc (ví dụ: tăng số lượng khám)"""
        doctor = DoctorFactory()
        tomorrow = date.today() + timedelta(days=1)
        schedule = Schedule.objects.create(
            doctor=doctor, date=tomorrow,
            start_time=time(8, 0), end_time=time(12, 0),
            max_patients=10
        )

        api_client.force_authenticate(user=doctor.user)
        url = reverse('schedule-detail', kwargs={'pk': schedule.id})
        payload = {"max_patients": 20} # Sửa số lượng

        response = api_client.patch(url, payload)
        
        assert response.status_code == status.HTTP_200_OK
        schedule.refresh_from_db()
        assert schedule.max_patients == 20

    # --- NEGATIVE TEST CASES (Các trường hợp lỗi/bị chặn) ---

    def test_create_schedule_in_past_fails(self, api_client):
        """Không thể tạo lịch cho ngày hôm qua"""
        doctor = DoctorFactory()
        api_client.force_authenticate(user=doctor.user)
        
        yesterday = date.today() - timedelta(days=1)
        payload = {
            "date": yesterday.isoformat(),
            "start_time": "08:00",
            "end_time": "12:00"
        }
        
        response = api_client.post(reverse('schedule-list'), payload)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "quá khứ" in str(response.data)

    def test_start_time_after_end_time_fails(self, api_client):
        """Giờ bắt đầu phải trước giờ kết thúc"""
        doctor = DoctorFactory()
        api_client.force_authenticate(user=doctor.user)
        
        payload = {
            "date": (date.today() + timedelta(days=1)).isoformat(),
            "start_time": "14:00",
            "end_time": "13:00" # Sai logic
        }
        
        response = api_client.post(reverse('schedule-list'), payload)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_create_duplicate_schedule_fails(self, api_client):
        """
        Test toàn vẹn dữ liệu: Một bác sĩ không thể tạo 2 lịch trong cùng 1 ngày.
        (Do unique_together = ('doctor', 'date') trong Model)
        """
        doctor = DoctorFactory()
        tomorrow = date.today() + timedelta(days=1)
        
        # Đã có lịch ngày mai
        Schedule.objects.create(
            doctor=doctor, date=tomorrow,
            start_time=time(8, 0), end_time=time(12, 0)
        )

        api_client.force_authenticate(user=doctor.user)
        # Cố tạo thêm lịch ngày mai
        payload = {
            "date": tomorrow.isoformat(),
            "start_time": "13:00",
            "end_time": "17:00"
        }
        response = api_client.post(reverse('schedule-list'), payload)

        # Kỳ vọng: 400 Bad Request
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_patient_cannot_create_schedule(self, api_client):
        """
        Test bảo mật: Bệnh nhân cố tình gọi API tạo lịch làm việc.
        Phải bị chặn (PermissionDenied).
        """
        patient = PatientFactory()
        api_client.force_authenticate(user=patient.user)
        
        url = reverse('schedule-list')
        payload = {
            "date": (date.today() + timedelta(days=1)).isoformat(),
            "start_time": "08:00",
            "end_time": "12:00"
        }
        
        response = api_client.post(url, payload)
        
        # Mong đợi: 403 Forbidden
        assert response.status_code == status.HTTP_403_FORBIDDEN