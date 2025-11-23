from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    birthday = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=10, choices=[("male","Male"),("female","Female")])
    address = models.CharField(max_length=255, blank=True, null=True)
    phone = models.CharField(max_length=15, unique=True, null=True, blank=True)
    avatar = models.TextField(null=True, blank=True)
    role = models.ForeignKey("Role", on_delete=models.SET_NULL, null=True, blank=True)
    recovery_token = models.CharField(max_length=255, null=True, blank=True)
    cccd = models.CharField(max_length=20, blank=True, null=True)
    ethinic_group = models.CharField(max_length=50, blank=True, null=True)
    
    def __str__(self):
        return f"{self.username} ({self.role})"


class Role(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name