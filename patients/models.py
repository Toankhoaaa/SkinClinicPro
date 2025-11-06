from django.db import models
from accounts.models import User

class Patient(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    health_insurance_number = models.CharField(max_length=50, blank=True, null=True)
    occupation = models.CharField(max_length=100, blank=True, null=True)
    medical_history = models.TextField(blank=True, null=True)
    def __str__(self):
        return f"Patient: {self.user.get_full_name() or self.user.username}"
