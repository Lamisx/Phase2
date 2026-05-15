from django.contrib import admin

from .models import (
    AuditLog,
    VerificationSession,
    VerificationChallenge,
    KeyUsageLog,
)


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):

    readonly_fields = [
        field.name for field in AuditLog._meta.fields
    ]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(VerificationSession)
class VerificationSessionAdmin(admin.ModelAdmin):

    readonly_fields = [
        field.name for field in VerificationSession._meta.fields
    ]


@admin.register(VerificationChallenge)
class VerificationChallengeAdmin(admin.ModelAdmin):

    readonly_fields = [
        field.name for field in VerificationChallenge._meta.fields
    ]


@admin.register(KeyUsageLog)
class KeyUsageLogAdmin(admin.ModelAdmin):

    readonly_fields = [
        field.name for field in KeyUsageLog._meta.fields
    ]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False