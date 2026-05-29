"""Admin registrations for device models."""
from django.contrib import admin

from .models import Device, DeviceKey, DeviceRevocationLog


@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    list_display = (
        "id", "user", "platform", "is_active",
        "is_primary_device", "is_trusted", "created_at",
    )
    search_fields = ("user__username", "user__email", "app_instance_id", "label")
    list_filter = ("platform", "is_active", "is_primary_device", "is_trusted")
    readonly_fields = ("id", "created_at", "updated_at")

#
@admin.register(DeviceKey)
class DeviceKeyAdmin(admin.ModelAdmin):
    list_display = (
        "id", "device", "organization", "key_purpose",
        "algorithm", "is_active", "created_at",
    )
    search_fields = ("device__id", "organization__name")
    list_filter = ("is_active", "algorithm", "key_purpose")
    readonly_fields = (
        "id", "created_at", "last_used_at", "revoked_at",
    )


@admin.register(DeviceRevocationLog)
class DeviceRevocationLogAdmin(admin.ModelAdmin):
    """Immutable audit log — no add/change, only view."""
    list_display = (
        "id", "device_id", "user_id",
        "revoked_by_actor_type", "created_at",
    )
    list_filter = ("revoked_by_actor_type",)
    readonly_fields = (
        "device_id", "user_id", "revoked_by_actor_type",
        "revoked_by_actor_id", "reason", "created_at",
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False