from django.db import models

class Device(models.Model):
    device_id = models.CharField(max_length=255, unique=True)
    status = models.CharField(max_length=20, default="PENDING")

    def __str__(self):
        return self.device_id