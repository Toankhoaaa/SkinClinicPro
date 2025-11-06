from django.db import models
from appointments.models import Appointment
from drugs.models import Drug

class Treatment(models.Model):
    appointment = models.ForeignKey(Appointment, on_delete=models.CASCADE)
    name = models.CharField(max_length=50)
    purpose = models.CharField(max_length=255)
    drug = models.ForeignKey(Drug, on_delete=models.SET_NULL, null=True, blank=True)
    dosage = models.CharField(max_length=50, null=True, blank=True)
    repeat_days = models.CharField(max_length=50, null=True, blank=True)
    repeat_time = models.TimeField(null=True, blank=True)
