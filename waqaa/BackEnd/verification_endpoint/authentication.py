import hashlib
import secrets

from django.conf import settings

from rest_framework import authentication
from rest_framework import exceptions

from organization_endpoints.models import Organization


def hash_api_key(api_key: str) -> str:

    pepper = getattr(settings, "API_KEY_PEPPER", "")

    if not pepper:
        raise RuntimeError(
            "API_KEY_PEPPER not configured in settings"
        )

    payload = (pepper + api_key).encode("utf-8")

    return hashlib.sha256(payload).hexdigest()


class OrganizationAPIKeyAuthentication(
    authentication.BaseAuthentication
):

    def authenticate(self, request):

        api_key = request.META.get("HTTP_X_API_KEY")

        if not api_key:
            return None

        api_key = api_key.strip()

        if len(api_key) < 20 or len(api_key) > 256:
            raise exceptions.AuthenticationFailed(
                "Invalid API key format"
            )

        try:
            hashed = hash_api_key(api_key)

        except RuntimeError:
            raise exceptions.AuthenticationFailed(
                "Server misconfiguration"
            )

        try:
            organization = Organization.objects.get(
                api_key_hash=hashed,
                is_active=True,
            )

        except Organization.DoesNotExist:
            raise exceptions.AuthenticationFailed(
                "Invalid API key"
            )

        if not secrets.compare_digest(
            organization.api_key_hash,
            hashed,
        ):
            raise exceptions.AuthenticationFailed(
                "Invalid API key"
            )

        request.organization = organization

        return (organization, None)

    def authenticate_header(self, request):

        return "X-API-Key"