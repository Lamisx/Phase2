# ممتاز ✅
from django.urls import path
from .views import (
    health_check,
    start_registration,
    complete_registration,
    login,
    create_delegate,
    list_delegates,
    delete_delegate,
)

app_name = "account"

urlpatterns = [
    path("health/", health_check, name="health-check"),
    path("auth/register/start/", start_registration, name="register-start"),
    path("auth/register/complete/", complete_registration, name="register-complete"),
    path("auth/login/", login, name="login"),
    path("delegations/", list_delegates, name="delegation-list"),
    path("delegations/create/", create_delegate, name="delegation-create"),
    path("delegations/<uuid:delegate_id>/revoke/", delete_delegate, name="delegation-revoke"),
]