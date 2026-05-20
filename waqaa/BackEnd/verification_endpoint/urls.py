"""Verification endpoint URL routes."""
from django.urls import path

from .views import (
    AuditLogListView,
    CancelSessionView,
    CreateSessionAndChallengeView,
    KeyUsageLogListView,
    ListSessionChallengesView,
    ListSessionsView,
    SessionStatusView,
    VerifyDecisionTokenView,
    VerifyDeviceSignatureView,
)


app_name = "verification"

urlpatterns = [
    path("sessions/",                                ListSessionsView.as_view(),            name="session-list"),
    path("sessions/create/",                         CreateSessionAndChallengeView.as_view(), name="session-create"),
    path("sessions/<uuid:session_id>/status/",       SessionStatusView.as_view(),           name="session-status"),
    path("sessions/<uuid:session_id>/cancel/",       CancelSessionView.as_view(),           name="session-cancel"),
    path("sessions/<uuid:session_id>/verify/",       VerifyDeviceSignatureView.as_view(),   name="session-verify"),
    path("sessions/<uuid:session_id>/verify-token/", VerifyDecisionTokenView.as_view(),     name="session-verify-token"),
    path("sessions/<uuid:session_id>/challenges/",   ListSessionChallengesView.as_view(),   name="session-challenges"),
    path("audit-logs/",                              AuditLogListView.as_view(),            name="audit-logs"),
    path("key-usage-logs/",                          KeyUsageLogListView.as_view(),         name="key-usage-logs"),
]