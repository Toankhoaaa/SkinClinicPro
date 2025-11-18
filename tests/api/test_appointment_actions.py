import pytest
from django.urls import reverse
from datetime import date, time, timedelta
from tests.factories.user_factory import PatientFactory, DoctorFactory
from appointments.models import Appointment
from availability.models import Schedule

@pytest.mark.django_db
class TestAppointmentActions:
    
    def test_patient_can_cancel_appointment(self, api_client):
        """Test bệnh nhân hủy lịch hẹn"""
        # 1. Setup: Tạo lịch hẹn cho ngày mai
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

        # 2. Action: Bệnh nhân gọi API hủy
        api_client.force_authenticate(user=patient.user)
        url = reverse('appointment-cancel-appointment', kwargs={'pk': appointment.id})
        response = api_client.patch(url)

        # 3. Verify
        assert response.status_code == 200
        appointment.refresh_from_db()
        assert appointment.status == 'canceled'

    def test_patient_can_reschedule(self, api_client):
        """Test bệnh nhân đổi lịch sang giờ khác"""
        # 1. Setup: Lịch hẹn cũ lúc 9h, muốn đổi sang 10h
        patient = PatientFactory()
        doctor = DoctorFactory()
        tomorrow = date.today() + timedelta(days=1)
        
        # Tạo Schedule cho bác sĩ để pass validation (quan trọng!)
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
            time=time(9, 0), # Giờ cũ
            status='pending'
        )

        # 2. Action: Đổi sang 10h00
        api_client.force_authenticate(user=patient.user)
        url = reverse('appointment-reschedule-appointment', kwargs={'pk': appointment.id})
        payload = {
            "date": tomorrow.isoformat(),
            "time": "10:00" # Giờ mới
        }
        response = api_client.patch(url, payload)

        # 3. Verify
        assert response.status_code == 200
        appointment.refresh_from_db()
        assert appointment.time == time(10, 0)

    def test_cancel_too_late_fails(self, api_client):
        """Test không thể hủy sát giờ (ví dụ quy định 12h trước khi khám)"""
        patient = PatientFactory()
        doctor = DoctorFactory()
        
        # Lịch hẹn là HÔM NAY, lúc này (sát giờ)
        appointment = Appointment.objects.create(
            patient=patient,
            doctor=doctor,
            date=date.today(), 
            time=time(23, 0), # Giả sử test chạy trong ngày
            status='pending'
        )
        
        # Mock thời gian thực tế là vấn đề khó, nhưng ở đây ta test logic
        # Nếu logic views.py chặn < 12h, thì test này sẽ trả về 400
        
        api_client.force_authenticate(user=patient.user)
        url = reverse('appointment-cancel-appointment', kwargs={'pk': appointment.id})
        response = api_client.patch(url)
        
        # Kỳ vọng lỗi 400 vì quá trễ để hủy
        assert response.status_code == 400