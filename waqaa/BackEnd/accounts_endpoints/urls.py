from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    CompleteRegistrationView,
    DelegationListCreateView,
    DelegationRevokeView,
    LoginThrottledTokenObtainPairView,
    MeView,
    StartRegistrationView,
    health_check,
)

app_name = "account"

urlpatterns = [
    path("health/", health_check, name="health-check"),
    path("auth/register/start/",StartRegistrationView.as_view(), name="register-start",),
    path("auth/register/complete/",CompleteRegistrationView.as_view(),name="register-complete",),
    path("auth/login/",LoginThrottledTokenObtainPairView.as_view(), name="token-obtain",),
    path("auth/token/refresh/",TokenRefreshView.as_view(),name="token-refresh",),
    path("me/", MeView.as_view(), name="me"),
    path("delegations/", DelegationListCreateView.as_view(), name="delegation-list-create",),
    path("delegations/<uuid:delegation_id>/revoke/",DelegationRevokeView.as_view(), name="delegation-revoke",),
]