from django.db import models
from accounts.models import User
from services.models import Service
from specialities.models import Speciality
from rooms.models import Room

class Doctor(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    specialty = models.ForeignKey(Speciality, on_delete=models.SET_NULL, null=True)
    room = models.ForeignKey(Room, on_delete=models.SET_NULL, null=True)
    price = models.IntegerField()
    description = models.TextField(null=True, blank=True)
    services = models.ManyToManyField(Service, related_name="doctors")
