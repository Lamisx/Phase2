from django.contrib import admin
from .models import Organization, OrganizationApiKey, OrganizationUser

admin.site.register(Organization)
admin.site.register(OrganizationApiKey)
admin.site.register(OrganizationUser)