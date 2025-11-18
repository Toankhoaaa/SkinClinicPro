import factory
from faker import Faker
from django.contrib.auth import get_user_model
from accounts.models import Role
from doctor.models import Doctor
from patients.models import Patient

User = get_user_model()
fake = Faker()

class RoleFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Role
        django_get_or_create = ('name',)
    name = 'Patient'

class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User
    
    username = factory.LazyAttribute(lambda x: fake.user_name())
    email = factory.LazyAttribute(lambda x: fake.email())
    role = factory.SubFactory(RoleFactory)

    @factory.post_generation
    def password(self, create, extracted, **kwargs):
        self.set_password('password123')

class DoctorFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Doctor
    
    user = factory.SubFactory(UserFactory, role__name='Doctor')
    price = 200000
    verificationStatus = "VERIFIED" 
    is_available = True

class PatientFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Patient
    
    user = factory.SubFactory(UserFactory, role__name='Patient')