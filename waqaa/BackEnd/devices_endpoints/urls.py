from django.urls import path
 
from . import views
 
 
app_name = "device"
 
urlpatterns = [
    # Devices
    path("create/", views.create_device, name="device-create"),
    path("me/",     views.list_my_devices, name="device-list"),
    path("<uuid:device_id>/revoke/", views.revoke_device, name="device-revoke"),
 
    # Device keys
    path("keys/register-device-key/", views.register_device_key, name="key-register"),
    path("keys/device/<uuid:device_id>/", views.list_device_keys, name="key-list"),
    path("keys/<uuid:device_key_id>/revoke/", views.revoke_device_key, name="key-revoke"),
 
    # Access decision (quick check)
    path("access-decision/", views.access_decision, name="access-decision"),
]
 # ابروح لدوره المياه