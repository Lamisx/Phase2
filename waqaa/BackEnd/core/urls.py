"""Root URL configuration."""
from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path


def health_check(_request):
    """Liveness probe — used by load balancers and uptime monitors."""
    return JsonResponse({"status": "ok"})


urlpatterns = [
    path("healthz/", health_check, name="health-check"),
    path("admin/", admin.site.urls),
    path("api/account/",      include("accounts_endpoints.urls")),
    path("api/organization/", include("organization_endpoints.urls")),
    path("api/device/",       include("devices_endpoints.urls")),
    path("api/verification/", include("verification_endpoint.urls")),
]
