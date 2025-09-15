from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    phone = models.CharField(max_length=15, unique=True)
    avatar = models.ImageField(upload_to="avatars/", null=True, blank=True)
    role = models.CharField(max_length=10, choices=[
        ("patient", "Patient"),
        ("doctor", "Doctor"),
        ("admin", "Admin"),
    ])
    recovery_token = models.CharField(max_length=255, null=True, blank=True)
    def __str__(self):
        return f"{self.username} ({self.role})"


