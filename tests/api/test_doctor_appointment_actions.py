import pytest
from django.urls import reverse
from rest_framework import status
from datetime import date, time, timedelta
from tests.factories.user_factory import DoctorFactory, PatientFactory
from appointments.models import Appointment

@pytest.mark.django_db
class TestDoctorAppointmentActions:
    
    # --- HAPPY PATHS (Thành công) ---

    def test_doctor_confirm_appointment(self, api_client):
        """Bác sĩ xác nhận lịch hẹn đang Pending thành công"""
        doctor = DoctorFactory()
        appointment = Appointment.objects.create(
            doctor=doctor,
            patient=PatientFactory(),
            date=date.today() + timedelta(days=1),
            time=time(9, 0),
            status='pending'
        )
        
        api_client.force_authenticate(user=doctor.user)
        url = reverse('appointment-confirm-appointment', kwargs={'pk': appointment.id})
        response = api_client.patch(url)
        
        assert response.status_code == status.HTTP_200_OK
        appointment.refresh_from_db()
        assert appointment.status == 'confirmed'

    def test_doctor_complete_appointment(self, api_client):
        """Bác sĩ hoàn thành lịch hẹn (đã Confirm) thành công"""
        doctor = DoctorFactory()
        appointment = Appointment.objects.create(
            doctor=doctor,
            patient=PatientFactory(),
            date=date.today(),
            time=time(9, 0),
            status='confirmed' # Tiền điều kiện: Phải confirm trước
        )
        
        api_client.force_authenticate(user=doctor.user)
        url = reverse('appointment-complete-appointment', kwargs={'pk': appointment.id})
        response = api_client.patch(url)
        
        assert response.status_code == status.HTTP_200_OK
        appointment.refresh_from_db()
        assert appointment.status == 'completed'

    # --- NEGATIVE TEST CASES (Các trường hợp lỗi) ---

    def test_other_doctor_cannot_confirm(self, api_client):
        """Bác sĩ A không thể xác nhận lịch của Bác sĩ B"""
        doctor_a = DoctorFactory()
        doctor_b = DoctorFactory()
        appointment = Appointment.objects.create(
            doctor=doctor_a,
            patient=PatientFactory(),
            date=date.today(), time=time(9, 0), status='pending'
        )
        
        api_client.force_authenticate(user=doctor_b.user) # Login bác sĩ B
        url = reverse('appointment-confirm-appointment', kwargs={'pk': appointment.id})
        response = api_client.patch(url)
        
        # Kỳ vọng: 403 Forbidden (Không có quyền)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_confirm_non_pending_appointment_fails(self, api_client):
        """
        Test logic: Chỉ có thể xác nhận lịch 'pending'.
        Nếu lịch đã hủy (canceled) hoặc đã xong (completed) thì không được xác nhận lại.
        """
        doctor = DoctorFactory()
        appointment = Appointment.objects.create(
            doctor=doctor, patient=PatientFactory(),
            date=date.today(), time=time(10, 0),
            status='canceled' # Lịch đã hủy
        )
        
        api_client.force_authenticate(user=doctor.user)
        url = reverse('appointment-confirm-appointment', kwargs={'pk': appointment.id})
        response = api_client.patch(url)
        
        # Kỳ vọng: 400 Bad Request (Validation Error)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Chỉ có thể xác nhận lịch hẹn 'pending'" in str(response.data)

    def test_complete_non_confirmed_appointment_fails(self, api_client):
        """
        Test logic: Chỉ có thể hoàn thành lịch 'confirmed'.
        Không thể nhảy cóc từ 'pending' sang 'completed'.
        """
        doctor = DoctorFactory()
        appointment = Appointment.objects.create(
            doctor=doctor, patient=PatientFactory(),
            date=date.today(), time=time(11, 0),
            status='pending' # Chưa confirm
        )
        
        api_client.force_authenticate(user=doctor.user)
        url = reverse('appointment-complete-appointment', kwargs={'pk': appointment.id})
        response = api_client.patch(url)
        
        # Kỳ vọng: 400 Bad Request
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Chỉ có thể hoàn thành lịch hẹn đã 'confirmed'" in str(response.data)

    def test_doctor_cannot_cancel_appointment(self, api_client):
        """
        Test phân quyền: Bác sĩ KHÔNG được quyền hủy lịch (chỉ bệnh nhân được hủy).
        """
        doctor = DoctorFactory()
        appointment = Appointment.objects.create(
            doctor=doctor, patient=PatientFactory(),
            date=date.today(), time=time(14, 0), status='pending'
        )
        
        api_client.force_authenticate(user=doctor.user)
        url = reverse('appointment-cancel-appointment', kwargs={'pk': appointment.id})
        response = api_client.patch(url)
        
        # Kỳ vọng: 403 Forbidden (Permission Denied)
        assert response.status_code == status.HTTP_403_FORBIDDEN