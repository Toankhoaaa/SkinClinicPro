from django.db import models
from appointments.models import Appointment

class BookingPhoto(models.Model):
    appointment = models.ForeignKey(Appointment, on_delete=models.CASCADE, related_name="photos")
    url = models.ImageField(upload_to="booking_photos/")
    uploaded_at = models.DateTimeField(auto_now_add=True)
