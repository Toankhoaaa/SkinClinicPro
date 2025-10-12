from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    phone = models.CharField(max_length=15, unique=True, null=True, blank=True)
    avatar = models.ImageField(upload_to="avatars/", null=True, blank=True)
    role = models.CharField(max_length=10, choices=[
        ("patient", "Patient"),
        ("doctor", "Doctor"),
        ("admin", "Admin"),
    ])
    recovery_token = models.CharField(max_length=255, null=True, blank=True)
    cccd = models.CharField(max_length=20, blank=True, null=True)  # Citizen ID
    ethinic_group = models.CharField(max_length=50, blank=True, null=True)
    
    def __str__(self):
        return f"{self.username} ({self.role})"


