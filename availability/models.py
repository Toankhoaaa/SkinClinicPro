# availability/models.py
from django.db import models
from doctor.models import Doctor

class Schedule(models.Model):
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name="schedules")
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_available = models.BooleanField(default=True)
    max_patients = models.IntegerField(default=10, null=True, blank=True)

    class Meta:
        # Đảm bảo một bác sĩ không thể tạo 2 lịch trùng ngày
        unique_together = ('doctor', 'date') 
        ordering = ['date', 'start_time']

    def __str__(self):
        return f"{self.doctor.user.username} - {self.date} ({self.start_time}-{self.end_time})"