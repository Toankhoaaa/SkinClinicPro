import pytest
from django.urls import reverse
from rest_framework import status
from datetime import date, time, timedelta
from django.utils import timezone
import datetime
from tests.factories.user_factory import PatientFactory, DoctorFactory
from appointments.models import Appointment
from availability.models import Schedule

@pytest.mark.django_db
class TestAppointmentActions:
    
    # --- HAPPY PATHS (Các trường hợp thành công) ---

    def test_patient_can_cancel_appointment(self, api_client):
        """Test bệnh nhân hủy lịch hẹn hợp lệ"""
        patient = PatientFactory()
        doctor = DoctorFactory()
        tomorrow = date.today() + timedelta(days=1)
        
        appointment = Appointment.objects.create(
            patient=patient,
            doctor=doctor,
            date=tomorrow,
            time=time(9, 0),
            status='pending'
        )

        api_client.force_authenticate(user=patient.user)
        url = reverse('appointment-cancel-appointment', kwargs={'pk': appointment.id})
        response = api_client.patch(url)

        assert response.status_code == status.HTTP_200_OK
        appointment.refresh_from_db()
        assert appointment.status == 'canceled'

    def test_patient_can_reschedule(self, api_client):
        """Test bệnh nhân đổi lịch sang giờ khác thành công"""
        patient = PatientFactory()
        doctor = DoctorFactory()
        tomorrow = date.today() + timedelta(days=1)
        
        # Tạo lịch làm việc (Schedule) để pass validation
        Schedule.objects.create(
            doctor=doctor,
            date=tomorrow,
            start_time=time(8, 0),
            end_time=time(17, 0)
        )

        appointment = Appointment.objects.create(
            patient=patient,
            doctor=doctor,
            date=tomorrow,
            time=time(9, 0),
            status='pending'
        )

        api_client.force_authenticate(user=patient.user)
        url = reverse('appointment-reschedule-appointment', kwargs={'pk': appointment.id})
        payload = {
            "date": tomorrow.isoformat(),
            "time": "10:00"
        }
        response = api_client.patch(url, payload)

        assert response.status_code == status.HTTP_200_OK
        appointment.refresh_from_db()
        assert appointment.time == time(10, 0)

    # --- NEGATIVE TEST CASES (Các trường hợp lỗi/bị chặn) ---

    def test_reschedule_to_booked_slot_fails(self, api_client):
        """
        Test đổi lịch vào khung giờ ĐÃ CÓ người khác đặt.
        Hệ thống phải ngăn chặn (Double Booking).
        """
        patient_1 = PatientFactory() # Người muốn đổi lịch
        patient_2 = PatientFactory() # Người đã đặt chỗ trước
        doctor = DoctorFactory()
        tomorrow = date.today() + timedelta(days=1)

        # Bác sĩ làm việc cả ngày
        Schedule.objects.create(
            doctor=doctor,
            date=tomorrow,
            start_time=time(8, 0),
            end_time=time(17, 0)
        )

        # Appointment 1: Của Patient 1 lúc 9:00
        appt_1 = Appointment.objects.create(
            patient=patient_1, doctor=doctor,
            date=tomorrow, time=time(9, 0), status='pending'
        )

        # Appointment 2: Của Patient 2 lúc 10:00 (Đã confirm)
        Appointment.objects.create(
            patient=patient_2, doctor=doctor,
            date=tomorrow, time=time(10, 0), status='confirmed'
        )

        # Patient 1 cố gắng đổi từ 9:00 sang 10:00 (Giờ của Patient 2)
        api_client.force_authenticate(user=patient_1.user)
        url = reverse('appointment-reschedule-appointment', kwargs={'pk': appt_1.id})
        payload = {
            "date": tomorrow.isoformat(),
            "time": "10:00" 
        }
        response = api_client.patch(url, payload)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'non_field_errors' in response.data
        assert response.data['non_field_errors'][0].code == 'unique'

    def test_reschedule_to_past_date_fails(self, api_client):
        """Test không thể đổi lịch về quá khứ"""
        patient = PatientFactory()
        doctor = DoctorFactory()
        today = date.today()
        
        appt = Appointment.objects.create(
            patient=patient, doctor=doctor,
            date=today + timedelta(days=2), # Ngày kia
            time=time(9, 0), status='pending'
        )

        yesterday = today - timedelta(days=1)
        
        api_client.force_authenticate(user=patient.user)
        url = reverse('appointment-reschedule-appointment', kwargs={'pk': appt.id})
        payload = {
            "date": yesterday.isoformat(),
            "time": "09:00"
        }
        response = api_client.patch(url, payload)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "quá khứ" in str(response.data)

    def test_cancel_too_late_fails(self, api_client):
        """Test hủy sát giờ (ví dụ quy định 12h trước khi khám)"""
        patient = PatientFactory()
        doctor = DoctorFactory()
        
        from django.utils import timezone
        import datetime
        
        # Tạo lịch hẹn cách hiện tại chỉ 1 tiếng (Vi phạm quy tắc >12h)
        now = timezone.now()
        start_time = (now + datetime.timedelta(hours=1)).time()
        
        appointment = Appointment.objects.create(
            patient=patient,
            doctor=doctor,
            date=now.date(), 
            time=start_time,
            status='pending'
        )
        
        api_client.force_authenticate(user=patient.user)
        url = reverse('appointment-cancel-appointment', kwargs={'pk': appointment.id})
        response = api_client.patch(url)
        
        # Kỳ vọng: 400 Bad Request
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_cancel_other_patient_appointment(self, api_client):
        """
        Test bảo mật (IDOR): Patient A cố tình hủy lịch của Patient B.
        Hệ thống phải trả về 404 Not Found (do lọc qua queryset của user).
        """
        patient_a = PatientFactory()
        patient_b = PatientFactory()
        doctor = DoctorFactory()
        
        # Lịch của Patient B
        appt_b = Appointment.objects.create(
            patient=patient_b, doctor=doctor,
            date=date.today() + timedelta(days=1),
            time=time(9, 0), status='pending'
        )
        
        # Patient A đăng nhập và cố hủy lịch B
        api_client.force_authenticate(user=patient_a.user)
        url = reverse('appointment-cancel-appointment', kwargs={'pk': appt_b.id})
        response = api_client.patch(url)
        
        # Kỳ vọng: 404 Not Found (Vì get_queryset chỉ trả về lịch của chính mình)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_cancel_too_late_fails(self, api_client):
        """Test hủy sát giờ (ví dụ quy định 12h trước khi khám)"""
        patient = PatientFactory()
        doctor = DoctorFactory()
        
        now = timezone.localtime()
        appt_time = (now + datetime.timedelta(hours=1)).time()
        
        appointment = Appointment.objects.create(
            patient=patient,
            doctor=doctor,
            date=now.date(), 
            time=appt_time,
            status='pending'
        )
        
        api_client.force_authenticate(user=patient.user)
        url = reverse('appointment-cancel-appointment', kwargs={'pk': appointment.id})
        response = api_client.patch(url)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST