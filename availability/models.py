from django.db import models
from doctor.models import Doctor


class Availability (models.Model):
    SLOT_STATUS = [
        ("AVAILABLE", "Available"),
        ("BOOKED", "Booked"),
        ("UNAVAILABLE", "Unavailable"),
    ]
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE)
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    status = models.CharField(
        max_length=20,
        choices=SLOT_STATUS,
        default="AVAILABLE"
    )
    
    class Meta:
        indexes = [
            models.Index(fields=["doctor", "start_time"]),
        ]
        ordering = ["start_time"]

    def __str__(self):
        return f"{self.doctor.user.first_name + self.doctor.user.last_name} - {self.start_time.strftime('%Y-%m-%d %H:%M')} ({self.status})"
