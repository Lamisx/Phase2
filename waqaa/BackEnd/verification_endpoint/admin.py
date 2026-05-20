"""Admin registrations for verification models."""
from django.contrib import admin

from .models import (
    AuditLog,
    KeyUsageLog,
    VerificationChallenge,
    VerificationSession,
)


@admin.register(VerificationSession)
class VerificationSessionAdmin(admin.ModelAdmin):
    list_display = (
        "id", "organization", "operation_type",
        "status", "attempt_count", "created_at",
    )
    list_filter = ("status", "operation_type")
    search_fields = ("org_operation_ref", "id")
    readonly_fields = [f.name for f in VerificationSession._meta.fields]


@admin.register(VerificationChallenge)
class VerificationChallengeAdmin(admin.ModelAdmin):
    list_display = (
        "id", "session", "attempt_number",
        "is_active", "is_used", "expires_at",
    )
    list_filter = ("is_active", "is_used")
    readonly_fields = [f.name for f in VerificationChallenge._meta.fields]


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    """Immutable audit log — view only."""
    list_display = (
        "id", "actor_type", "action", "result",
        "organization_id", "session_id", "created_at",
    )
    list_filter = ("actor_type", "result", "action")
    search_fields = ("session_id", "organization_id", "device_id", "actor_id")
    readonly_fields = [f.name for f in AuditLog._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(KeyUsageLog)
class KeyUsageLogAdmin(admin.ModelAdmin):
    """Immutable key-usage log — view only."""
    list_display = (
        "id", "action", "result",
        "organization_id", "device_id", "session_id", "created_at",
    )
    list_filter = ("action", "result")
    search_fields = ("session_id", "organization_id", "device_id", "device_key_id")
    readonly_fields = [f.name for f in KeyUsageLog._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False