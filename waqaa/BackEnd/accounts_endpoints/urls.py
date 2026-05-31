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
    list_received_delegations,   # ← مُضاف
    revoke_my_delegation,        # ← مُضاف
)

app_name = "account"


urlpatterns = [
    path("health/", health_check, name="health"),

    # ===== Auth =====
    path("auth/register/start/",           start_registration,    name="register-start"),
    path("auth/register/verify-identity/", verify_identity,       name="register-verify-identity"),
    path("auth/register/complete/",        complete_registration, name="register-complete"),
    path("auth/login/",                    login,                 name="login"),

    # ===== Me =====
    path("me/", me, name="me"),

    # ===== Delegations (A = المُفوِّض) =====
    path("delegations/",                              list_delegations,  name="delegation-list"),
    path("delegations/create/",                       create_delegation, name="delegation-create"),
    path("delegations/<uuid:delegation_id>/revoke/",  revoke_delegation, name="delegation-revoke"),
    path("delegations/generate-code/",                generate_delegation_code, name="delegation-generate-code"),
    path("delegations/accept-code/",                  accept_delegation_code,   name="delegation-accept-code"),

    # ===== Delegations (B = المُفوَّض) =====  ← مُضاف
    path(
        "delegations/received/",
        list_received_delegations,
        name="delegation-received",
    ),
    path(
        "delegations/<uuid:delegation_id>/revoke-as-delegated/",
        revoke_my_delegation,
        name="delegation-revoke-as-delegated",
    ),
]