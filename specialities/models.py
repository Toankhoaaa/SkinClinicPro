from django.db import models

class Speciality(models.Model):
    name = models.CharField(max_length=50)
    description = models.TextField()
    image = models.ImageField(upload_to="specialities/", null=True, blank=True)
