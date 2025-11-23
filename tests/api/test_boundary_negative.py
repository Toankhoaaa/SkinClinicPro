import pytest
from django.urls import reverse
from rest_framework import status
from datetime import date, time, timedelta
from tests.factories.user_factory import PatientFactory, DoctorFactory
from availability.models import Schedule
from appointments.models import Appointment

@pytest.mark.django_db
class TestBoundaryAndNegative:

    # --- BOUNDARY TESTING (Kiểm thử biên) ---
    
    def test_max_patients_boundary(self, api_client):
        """
        Test biên: Đặt lịch khi đã đạt giới hạn max_patients.
        Kịch bản: Bác sĩ chỉ nhận 1 khách/ngày. Khách thứ 2 đặt sẽ bị từ chối.
        """
        # 1. Setup: Bác sĩ giới hạn max_patients = 1
        doctor = DoctorFactory()
        patient_1 = PatientFactory()
        patient_2 = PatientFactory()
        tomorrow = date.today() + timedelta(days=1)
        
        Schedule.objects.create(
            doctor=doctor,
            date=tomorrow,
            start_time=time(8, 0),
            end_time=time(17, 0),
            max_patients=1  # <--- GIÁ TRỊ BIÊN
        )

        # 2. Khách 1 đặt thành công
        Appointment.objects.create(
            doctor=doctor, 
            patient=patient_1, 
            date=tomorrow, 
            time=time(9, 0), 
            status='confirmed'
        )

        # 3. Khách 2 cố đặt (Cùng ngày, giờ khác)
        api_client.force_authenticate(user=patient_2.user)
        url = reverse('appointment-list')
        payload = {
            "doctor_id": doctor.id,
            "date": tomorrow.isoformat(),
            "time": "10:00"
        }
        response = api_client.post(url, payload)

        # 4. Verify: Phải bị từ chối (400 Bad Request)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "đạt số lượng bệnh nhân tối đa" in str(response.data)

    # --- NEGATIVE TESTING (Kiểm thử sai/ngược) ---

    def test_booking_with_past_date(self, api_client):
        """Test đặt lịch ngày quá khứ (Logic sai)"""
        patient = PatientFactory()
        doctor = DoctorFactory()
        yesterday = date.today() - timedelta(days=1)

        api_client.force_authenticate(user=patient.user)
        url = reverse('appointment-list')
        payload = {
            "doctor_id": doctor.id,
            "date": yesterday.isoformat(), # Ngày hôm qua
            "time": "09:00"
        }
        response = api_client.post(url, payload)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "quá khứ" in str(response.data)

    def test_access_without_token(self, api_client):
        """Test bảo mật: Gọi API mà không có Token"""
        url = reverse('patient-me') # API yêu cầu đăng nhập
        response = api_client.get(url)
        
        # Kỳ vọng: 401 Unauthorized
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_create_notification_string_overflow(self, api_client):
        """
        Case Study: Tái hiện lỗi 'value too long' bạn vừa fix.
        Thử tạo thông báo với type dài > 50 ký tự xem DB có chấp nhận không.
        (Sau khi bạn fix max_length=50 thì test này phải PASS nếu chuỗi < 50)
        """
        from notifications.models import Notification
        patient = PatientFactory()
        
        # Chuỗi 45 ký tự (hợp lệ với fix mới, nhưng sẽ lỗi với code cũ 20)
        long_type = "A" * 45 
        
        try:
            Notification.objects.create(
                user=patient.user,
                message="Test message",
                type=long_type
            )
            success = True
        except Exception:
            success = False
            
        assert success is True