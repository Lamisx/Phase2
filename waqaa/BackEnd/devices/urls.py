from django.urls import path
from .views.auth_views import health_check, register,login
from .views.device_views import access_decision, create_device, list_devices,revoke_device
from .views.delegate_views import create_delegate, list_delegates, delete_delegate
from .views.session_views import create_session,verify_session ,get_session_status,cancel_session
from .views.device_key_views import register_device_key,list_device_keys,revoke_device_key



urlpatterns = [
    path("health/", health_check),
    path("auth/register/", register),
    path("auth/login/", login),

    path("devices/create/", create_device),
    path("devices/<uuid:user_id>/", list_devices),
    path("access/decision/", access_decision),# it is just pre-check


    path("delegates/", list_delegates),
    path("delegates/create/", create_delegate),
    path("delegates/<uuid:delegate_id>/", delete_delegate),

    path("devices/<uuid:device_id>/revoke/", revoke_device),
    path("devices/<uuid:device_id>/keys/", list_device_keys),
    path("device-keys/<uuid:device_key_id>/revoke/", revoke_device_key),

    path("sessions/", create_session),
    path("sessions/<uuid:session_id>/verify/", verify_session),
    path("sessions/<uuid:session_id>/", get_session_status),
    path("sessions/<uuid:session_id>/cancel/", cancel_session),

    path("devices/<uuid:device_id>/keys/",register_device_key),

]