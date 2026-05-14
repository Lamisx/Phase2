from django.contrib import admin
from .models import AccountUser, UserDelegation

admin.site.register(AccountUser)
admin.site.register(UserDelegation)