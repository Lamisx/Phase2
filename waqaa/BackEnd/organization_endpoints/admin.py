from django.contrib import admin

from .models import Organization, OrganizationApiKey, OrganizationUser 


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "status", "created_at")
    search_fields = ("name",)
    list_filter = ("status",)
    readonly_fields = ("id", "created_at", "updated_at")


@admin.register(OrganizationApiKey)
class OrganizationApiKeyAdmin(admin.ModelAdmin):
    list_display = (
        "id", "organization", "label", "is_active",
        "rate_limit_per_minute", "created_at",
    )
    list_filter = ("is_active", "organization")
    search_fields = ("label", "organization__name")
    readonly_fields = (
        "id",
        "key_hash",
        "last_used_at",
        "revoked_at",
        "created_at",
        "updated_at",
    )


@admin.register(OrganizationUser)
class OrganizationUserAdmin(admin.ModelAdmin):
    list_display = ("id", "organization", "user", "role", "status", "created_at")
    list_filter = ("role", "status", "organization")
    search_fields = ("external_user_ref", "user__username")
    readonly_fields = ("id", "created_at", "updated_at")

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):

    readonly_fields = [field.name for field in AuditLog._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False