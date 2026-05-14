"""
API key authentication for organizations.
 
Replaces the previous global middleware. Plug into a view via:
 
    class MyView(APIView):
        authentication_classes = [OrganizationAPIKeyAuthentication]
        permission_classes = [HasOrganizationAPIKey, HasScope]
        required_scope = OrganizationApiKey.SCOPE_AUDIT_READ
 
On success the request gets:
    request.auth          — OrganizationApiKey instance (DRF standard)
    request.organization  — Organization instance (convenience)
    request.api_key       — alias for request.auth (convenience)
"""
from django.contrib.auth.models import AnonymousUser
from django.utils import timezone
from rest_framework import authentication, exceptions
 
from core.utils_crypto import hash_api_key
 
from .models import Organization, OrganizationApiKey
 
 
class OrganizationAPIKeyAuthentication(authentication.BaseAuthentication):
    """Authenticate via X-API-Key header.
 
    The plaintext key from the header is HMAC-hashed before lookup, so we
    never compare against the raw value the client sent.
    """
 
    HEADER_NAME = "HTTP_X_API_KEY"
 
    def authenticate(self, request):
        raw_key = (request.META.get(self.HEADER_NAME) or "").strip()
        if not raw_key:
            # No header — let other auth classes try (or DRF treats as anonymous).
            return None
 
        # Reject obviously malformed keys early.
        if not (16 <= len(raw_key) <= 256):
            raise exceptions.AuthenticationFailed("Invalid API key format")
 
        key_hash = hash_api_key(raw_key)
 
        try:
            api_key = (
                OrganizationApiKey.objects
                .select_related("organization")
                .get(
                    key_hash=key_hash,
                    is_active=True,
                    revoked_at__isnull=True,
                )
            )
        except OrganizationApiKey.DoesNotExist:
            raise exceptions.AuthenticationFailed("Invalid or revoked API key")
 
        if api_key.expires_at and api_key.expires_at < timezone.now():
            raise exceptions.AuthenticationFailed("API key expired")
 
        if api_key.organization.status != Organization.STATUS_ACTIVE:
            raise exceptions.AuthenticationFailed("Organization is not active")
 
        # Fire-and-forget update of last_used_at.
        # Using .update() avoids the read-modify-write race.
        OrganizationApiKey.objects.filter(pk=api_key.pk).update(
            last_used_at=timezone.now()
        )
 
        # Convenience attributes for views.
        request.organization = api_key.organization
        request.api_key = api_key
 
        # DRF expects (user, auth). We use AnonymousUser because this is
        # machine-to-machine auth — no end-user is signed in.
        return (AnonymousUser(), api_key)
 
    def authenticate_header(self, request):
        return "X-API-Key"