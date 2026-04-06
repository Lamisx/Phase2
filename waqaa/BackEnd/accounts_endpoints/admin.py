from django.contrib import admin
from .models import WaqaUser, DelegatedAccess

admin.site.register(WaqaUser)
admin.site.register(DelegatedAccess)