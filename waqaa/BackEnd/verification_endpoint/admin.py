from django.contrib import admin
from .models import  AuditLog, VerificationSession, VerificationChallenge, KeyUsageLog

admin.site.register(AuditLog)
admin.site.register(VerificationSession)
admin.site.register(VerificationChallenge)
admin.site.register(KeyUsageLog)
