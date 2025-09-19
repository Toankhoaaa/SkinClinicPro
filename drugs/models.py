from django.db import models

class Drug(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
