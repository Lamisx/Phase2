from django.urls import path
from . import views

urlpatterns = [
    path("health/", views.health_check),
    path("register/", views.register),
    path("login/", views.login),

    path("delegates/", views.list_delegates),
    path("delegates/create/", views.create_delegate),
    path("delegates/<uuid:delegate_id>/delete/", views.delete_delegate),
]