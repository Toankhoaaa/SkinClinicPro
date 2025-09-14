from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    # Thêm vai trò để phân loại
    ROLE_CHOICES = (
        ("patient", "Patient"),
        ("doctor", "Doctor"),
        ("staff", "Staff"),
        ("admin", "Admin"),
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="patient")
    phone = models.CharField(max_length=15, blank=True, null=True)
    avatar = models.ImageField(upload_to="avatars/", blank=True, null=True)

    def __str__(self):
        return f"{self.username} - {self.role}"


class PatientProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="patient_profile")
    birthday = models.DateField(blank=True, null=True)
    gender = models.CharField(max_length=10, choices=[("male", "Male"), ("female", "Female")])
    address = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"Patient: {self.user.username}"


class DoctorProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="doctor_profile")
    specialty = models.ForeignKey("clinics.Speciality", on_delete=models.SET_NULL, null=True, blank=True)
    room = models.ForeignKey("clinics.Room", on_delete=models.SET_NULL, null=True, blank=True)
    description = models.TextField(blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        return f"Dr. {self.user.username} - {self.specialty}"

