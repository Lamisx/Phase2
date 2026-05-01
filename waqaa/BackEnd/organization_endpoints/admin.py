from django.contrib import admin
from .models import Organization, OrganizationApiKey, OrganizationUser

#admin.site.register(Organization)
#admin.site.register(OrganizationApiKey)
#admin.site.register(OrganizationUser)
# =========================
# Organization
# =========================
@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "status", "created_at")
    search_fields = ("name",)
    list_filter = ("status",)


# =========================
# API Key
# =========================
@admin.register(OrganizationApiKey)
class OrganizationApiKeyAdmin(admin.ModelAdmin):
    list_display = ("id", "organization", "is_active", "rate_limit_per_minute", "created_at")
    readonly_fields = ("key_hash",)
    list_filter = ("is_active",)
    readonly_fields = ("key_hash",)


# =========================
# Organization User
# =========================
@admin.register(OrganizationUser)
class OrganizationUserAdmin(admin.ModelAdmin):
    list_display = ("id", "organization", "user", "role", "status")
    search_fields = ("external_user_ref",)
    list_filter = ("role", "status")