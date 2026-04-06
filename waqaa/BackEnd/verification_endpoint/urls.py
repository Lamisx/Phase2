from django.urls import path
from . import views

urlpatterns = [

    # ─── Session ──────────────────────────────────────
    path("sessions/create/",                    views.create_session,     name="create_session"),
    path("sessions/<uuid:session_id>/verify/",  views.verify_session,     name="verify_session"),
    path("sessions/<uuid:session_id>/status/",  views.get_session_status, name="get_session_status"),
    path("sessions/<uuid:session_id>/cancel/",  views.cancel_session,     name="cancel_session"),
]