# from django.urls import path
# from .views import health_check

# urlpatterns = [
#     path("health/", health_check),
# ]from django.urls import path
from .views import access_decision
from django.urls import path
urlpatterns = [
    path("access/decision/", access_decision),
]

