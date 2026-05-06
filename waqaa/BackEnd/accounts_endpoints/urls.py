from django.urls import path
from . import views

urlpatterns = [
    path("health/", views.health_check),
    path("register/", views.register),
    path("login/", views.login),
    path("idRegister/", views.start_registration),
    path("chekNafath/", views.mock_nafath),
    path("userPas/", views.set_credentials),
    path("phEm/", views.set_contact),
    path("SignIn/", views.complete_registration),
    

    path("delegates/", views.list_delegates),
    path("delegates/create/", views.create_delegate),
    path("delegates/<uuid:delegate_id>/delete/", views.delete_delegate),
]