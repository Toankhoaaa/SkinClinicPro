import factory
from specialities.models import Speciality
from rooms.models import Room
from drugs.models import Drug

class SpecialityFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Speciality
        django_get_or_create = ('name',)

    name = factory.Sequence(lambda n: f"Speciality {n}")
    description = factory.Faker('text', max_nb_chars=100)
    # image = ... (Có thể bỏ qua hoặc dùng file dummy nếu cần)

class RoomFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Room
        django_get_or_create = ('name',)

    name = factory.Sequence(lambda n: f"Room {n}")
    location = "Tầng 2, Khu A"

class DrugFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Drug
        django_get_or_create = ('name',)

    name = factory.Sequence(lambda n: f"Thuốc {n}")
    description = "Uống sau khi ăn"