import pytest
from django.urls import reverse
from rest_framework import status
from datetime import date, time
from tests.factories.user_factory import DoctorFactory, PatientFactory
from appointments.models import Appointment
from treatments.models import Treatment

@pytest.mark.django_db
class TestTreatments:
    
    # --- HAPPY PATHS (Trường hợp thành công) ---

    def test_doctor_create_treatment_success(self, api_client):
        """Bác sĩ kê đơn thuốc cho bệnh nhân thành công"""
        doctor = DoctorFactory()
        patient = PatientFactory()
        appointment = Appointment.objects.create(
            doctor=doctor, patient=patient, 
            date=date.today(), time=time(10,0), status='confirmed'
        )
        
        api_client.force_authenticate(user=doctor.user)
        url = reverse('treatment-list')
        payload = {
            "appointment_id": appointment.id,
            "name": "Phác đồ trị mụn",
            "purpose": "Giảm viêm",
            "dosage": "2 viên/ngày"
        }
        
        response = api_client.post(url, payload)
        assert response.status_code == status.HTTP_201_CREATED
        assert Treatment.objects.count() == 1
        assert Treatment.objects.first().appointment == appointment

    def test_doctor_update_own_treatment(self, api_client):
        """Bác sĩ có thể chỉnh sửa phác đồ do chính mình tạo"""
        doctor = DoctorFactory()
        patient = PatientFactory()
        appointment = Appointment.objects.create(
            doctor=doctor, patient=patient, 
            date=date.today(), time=time(10,0), status='confirmed'
        )
        treatment = Treatment.objects.create(
            appointment=appointment, name="Kê đơn cũ", purpose="Test"
        )
        
        api_client.force_authenticate(user=doctor.user)
        url = reverse('treatment-detail', kwargs={'pk': treatment.id})
        payload = {"name": "Kê đơn mới (Updated)"}
        
        response = api_client.patch(url, payload)
        assert response.status_code == status.HTTP_200_OK
        treatment.refresh_from_db()
        assert treatment.name == "Kê đơn mới (Updated)"

    # --- NEGATIVE / SECURITY CASES (Trường hợp lỗi/bảo mật) ---

    def test_patient_cannot_create_treatment(self, api_client):
        """Bệnh nhân không được phép tự kê đơn"""
        patient = PatientFactory()
        doctor = DoctorFactory()
        appointment = Appointment.objects.create(
            doctor=doctor, patient=patient, 
            date=date.today(), time=time(10,0), status='confirmed'
        )
        
        api_client.force_authenticate(user=patient.user) # Login bệnh nhân
        url = reverse('treatment-list')
        payload = {
            "appointment_id": appointment.id,
            "name": "Tự kê đơn",
            "purpose": "Test"
        }
        
        response = api_client.post(url, payload)
        # Mong đợi: 403 Forbidden
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_doctor_cannot_create_treatment_for_other_doctor_appointment(self, api_client):
        """
        Bác sĩ A không được phép kê đơn cho lịch hẹn của Bác sĩ B.
        Đây là quy tắc nghiệp vụ quan trọng.
        """
        doctor_a = DoctorFactory()
        doctor_b = DoctorFactory()
        patient = PatientFactory()
        
        # Lịch hẹn thuộc về Bác sĩ B
        appointment_b = Appointment.objects.create(
            doctor=doctor_b, patient=patient,
            date=date.today(), time=time(14,0), status='confirmed'
        )

        # Bác sĩ A đăng nhập và cố kê đơn
        api_client.force_authenticate(user=doctor_a.user)
        url = reverse('treatment-list')
        payload = {
            "appointment_id": appointment_b.id,
            "name": "Kê đơn trộm",
            "purpose": "Vi phạm"
        }

        response = api_client.post(url, payload)
        
        # Mong đợi: 403 Forbidden (Do logic check trong perform_create)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_doctor_cannot_access_other_doctor_treatment(self, api_client):
        """
        Bác sĩ A không thể xem/sửa phác đồ của Bác sĩ B.
        """
        doctor_a = DoctorFactory()
        doctor_b = DoctorFactory()
        patient = PatientFactory()
        
        # Phác đồ của Bác sĩ B
        appointment_b = Appointment.objects.create(
            doctor=doctor_b, patient=patient,
            date=date.today(), time=time(15,0), status='confirmed'
        )
        treatment_b = Treatment.objects.create(
            appointment=appointment_b, name="Đơn thuốc B", purpose="Test"
        )

        # Bác sĩ A đăng nhập và cố xem/sửa
        api_client.force_authenticate(user=doctor_a.user)
        url = reverse('treatment-detail', kwargs={'pk': treatment_b.id})
        
        response = api_client.get(url)
        
        # Mong đợi: 404 Not Found (Vì get_queryset đã lọc chỉ trả về data của chính mình)
        assert response.status_code == status.HTTP_404_NOT_FOUND