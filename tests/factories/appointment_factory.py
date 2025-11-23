import factory
import datetime
from availability.models import Schedule
from appointments.models import Appointment
from records.models import AppointmentRecord
from .user_factory import DoctorFactory, PatientFactory

class ScheduleFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Schedule

    doctor = factory.SubFactory(DoctorFactory)
    date = factory.LazyFunction(datetime.date.today)
    start_time = datetime.time(8, 0)
    end_time = datetime.time(17, 0)
    is_available = True
    max_patients = 10

class AppointmentFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Appointment

    patient = factory.SubFactory(PatientFactory)
    doctor = factory.SubFactory(DoctorFactory)
    date = factory.LazyFunction(datetime.date.today)
    time = datetime.time(9, 0)
    status = 'pending'
    notes = factory.Faker('sentence')

class AppointmentRecordFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = AppointmentRecord
    
    appointment = factory.SubFactory(AppointmentFactory)
    reason = "Đau đầu, chóng mặt"
    description = "Bệnh nhân có dấu hiệu thiếu ngủ"
    status_before = "Mệt mỏi"
    status_after = "Đã kê đơn thuốc"