from django.urls import path
from . import views

urlpatterns = [
    path("create/", views.create_device),
    path("user/<uuid:user_id>/", views.list_devices),
    path("<uuid:device_id>/revoke/", views.revoke_device),

    path("keys/register/", views.register_device_key),
    path("keys/device/<uuid:device_id>/", views.list_device_keys),
    path("keys/<uuid:device_key_id>/revoke/", views.revoke_device_key),

    path("sessions/create/", views.create_session),
    path("sessions/<uuid:session_id>/verify/", views.verify_session),
    path("sessions/<uuid:session_id>/status/", views.get_session_status),
    path("sessions/<uuid:session_id>/cancel/", views.cancel_session),
]