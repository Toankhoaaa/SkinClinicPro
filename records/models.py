from django.db import models
from appointments.models import Appointment

class AppointmentRecord(models.Model):
    appointment = models.OneToOneField(Appointment, on_delete=models.CASCADE)
    reason = models.CharField(max_length=100, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    status_before = models.TextField(null=True, blank=True)
    status_after = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
