from django.urls import path

from . import views

urlpatterns = [
    path("create/", views.create_device),
    path("me/", views.list_my_devices),
    path("<uuid:device_id>/revoke/", views.revoke_device),

    path("keys/register/", views.register_device_key),
    path(
        "keys/device/<uuid:device_id>/",
        views.list_device_keys,
    ),
    path(
        "keys/<uuid:device_key_id>/revoke/",
        views.revoke_device_key,
    ),

    path("access-decision/", views.access_decision),
]