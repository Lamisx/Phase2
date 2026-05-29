# ممتاز ✅
from django.urls import path
from .views import (
    complete_registration,
    create_delegation,
    health_check,
    list_delegations,
    login,
    me,
    revoke_delegation,
    start_registration,
    verify_identity,
    generate_delegation_code,
    accept_delegation_code,
)

app_name = "account"


urlpatterns = [
    path("health/", health_check, name="health"),
    path("auth/register/start/",           start_registration,    name="register-start"),
    path("auth/register/verify-identity/", verify_identity,       name="register-verify-identity"),
    path("auth/register/complete/",        complete_registration, name="register-complete"),
    path("auth/login/", login, name="login"),
    path("me/", me, name="me"),
    path("delegations/",                                  list_delegations,  name="delegation-list"),
    path("delegations/create/",                           create_delegation, name="delegation-create"),
    path("delegations/<uuid:delegation_id>/revoke/",      revoke_delegation, name="delegation-revoke"),
    path(
    "delegations/generate-code/",
    generate_delegation_code,
    name="delegation-generate-code",
    
),
path(
    "delegations/accept-code/",
    accept_delegation_code,
    name="delegation-accept-code",
),
]