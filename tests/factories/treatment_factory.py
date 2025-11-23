import factory
from treatments.models import Treatment
from notifications.models import Notification
from .appointment_factory import AppointmentFactory
from .clinic_factory import DrugFactory
from .user_factory import UserFactory

class TreatmentFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Treatment

    appointment = factory.SubFactory(AppointmentFactory)
    name = "Điều trị cơ bản"
    purpose = "Giảm triệu chứng"
    drug = factory.SubFactory(DrugFactory)
    dosage = "2 viên/ngày"
    repeat_days = "5 ngày"
    repeat_time = None

class NotificationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Notification

    user = factory.SubFactory(UserFactory)
    message = factory.Faker('sentence')
    type = "system_alert"
    is_read = False