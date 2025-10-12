from django.db import models
from accounts.models import User
from specialities.models import Speciality
from rooms.models import Room

class Doctor(models.Model):
    VERIFICATION_STATUS_CHOICES = [
        ("PENDING", "Pending"),     # Đang chờ xác minh
        ("VERIFIED", "Verified"),   # Đã xác minh
        ("REJECTED", "Rejected"),   # Bị từ chối
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    specialty = models.ForeignKey(Speciality, on_delete=models.SET_NULL, null=True)
    room = models.ForeignKey(Room, on_delete=models.SET_NULL, null=True)
    price = models.IntegerField()
    experience = models.IntegerField(null=True, blank=True)
    credentiaUrl = models.URLField(max_length=255, null=True, blank=True)
    verificationStatus = models.CharField(
        max_length=10,
        choices=VERIFICATION_STATUS_CHOICES,
        default="PENDING"
    )
    description = models.TextField(null=True, blank=True)
