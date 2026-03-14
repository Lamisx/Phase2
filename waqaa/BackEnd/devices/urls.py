from django.urls import path
from .views.auth_views import health_check, register,login
from .views.device_views import access_decision, create_device, list_devices
from .views.delegate_views import create_delegate, list_delegates, delete_delegate







urlpatterns = [
    path("health/", health_check),
    path("auth/register/", register),
    path("auth/login/", login),

    path("devices/create/", create_device),
    path("devices/<uuid:user_id>/", list_devices),
    path("access/decision/", access_decision),

    path("delegates/", list_delegates),
    path("delegates/create/", create_delegate),
    path("delegates/<uuid:delegate_id>/", delete_delegate),
]