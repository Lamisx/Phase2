from django.contrib import admin
from .models import Device, DeviceKey, VerificationSession, VerificationChallenge

admin.site.register(Device)
admin.site.register(DeviceKey)
admin.site.register(VerificationSession)
admin.site.register(VerificationChallenge)