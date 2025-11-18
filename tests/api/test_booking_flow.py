import pytest
from django.urls import reverse
from datetime import date, time, timedelta
from tests.factories.user_factory import PatientFactory, DoctorFactory
from availability.models import Schedule

@pytest.mark.django_db
class TestBookingFlow:
    
    def test_patient_can_book_appointment_successfully(self, api_client):
        patient = PatientFactory()
        doctor = DoctorFactory()
        
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

        assert response.status_code == 201
        assert response.data['status'] == 'pending'
        assert response.data['doctor']['id'] == doctor.id

    def test_cannot_book_outside_schedule(self, api_client):
        patient = PatientFactory()
        doctor = DoctorFactory()
        
        Schedule.objects.create(
            doctor=doctor,
            date=date.today() + timedelta(days=1),
            start_time=time(8, 0),
            end_time=time(17, 0)
        )
        
        api_client.force_authenticate(user=patient.user)
        response = api_client.post(reverse('appointment-list'), {
            "doctor_id": doctor.id,
            "date": (date.today() + timedelta(days=1)).isoformat(),
            "time": "20:00"
        })
        
        assert response.status_code == 400
        assert "Giờ hẹn phải nằm trong khoảng làm việc" in str(response.data)