"""
Organization endpoints.

The organization is identified by the X-API-Key header. No path or
query parameter ever decides which organization a request operates on
— this prevents cross-organization data leaks.

Public endpoints (no auth):
    GET  /api/organization/public/        — list active organizations

Authenticated endpoints (X-API-Key):
    GET  /api/organization/me/            — return calling org
    GET  /api/organization/api-keys/      — list calling org's keys
    POST /api/organization/links/         — link a user to calling org
    GET  /api/organization/links/list/    — list calling org's linked users
"""
from django.db import IntegrityError
from rest_framework import status, permissions
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts_endpoints.models import AccountUser
from core.utils_crypto import hash_national_id_storage

from .authentication import OrganizationAPIKeyAuthentication
from .models import Organization, OrganizationApiKey, OrganizationUser
from .permissions import HasOrganizationAPIKey, HasScope
from .serializers import (
    LinkUserSerializer,
    OrganizationApiKeySerializer,
    OrganizationSerializer,
    OrganizationUserSerializer,
)
from devices_endpoints.models import Device, DeviceKey


# ============================================================
# Public listing (no auth)
# ============================================================
class PublicOrganizationListView(APIView):
    """GET /api/organization/public/ — list active organizations.

    Public endpoint so mobile clients can show users a picker when
    registering a device key. Only active organizations are returned.
    """

    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request):
        orgs = Organization.objects.filter(status=Organization.STATUS_ACTIVE)
        serializer = OrganizationSerializer(orgs, many=True)
        return Response({
            "count": len(serializer.data),
            "organizations": serializer.data,
        })


# ============================================================
# Organization self-info
# ============================================================
class OrganizationSelfView(APIView):
    """GET /api/organization/me/ — return the organization identified by the key."""

    authentication_classes = [OrganizationAPIKeyAuthentication]
    permission_classes = [HasOrganizationAPIKey]

    def get(self, request):
        return Response(OrganizationSerializer(request.organization).data)


# ============================================================
# API keys (read-only listing)
# ============================================================
class OrganizationApiKeyListView(APIView):
    """GET /api/organization/api-keys/ — list keys for the calling org."""

    authentication_classes = [OrganizationAPIKeyAuthentication]
    permission_classes = [HasOrganizationAPIKey, HasScope]
    required_scope = OrganizationApiKey.SCOPE_AUDIT_READ

    def get(self, request):
        keys = (
            OrganizationApiKey.objects
            .filter(organization=request.organization)
            .order_by("-created_at")
        )
        return Response({
            "count": keys.count(),
            "api_keys": OrganizationApiKeySerializer(keys, many=True).data,
        })


# ============================================================
# Link a Waqa user to the organization (B2B integration)
# ============================================================
class LinkUserView(APIView):
    """POST /api/organization/links/ — link a Waqa user to the calling org.

    Integration flow (B2B):
        1. User opens the bank's app and tries to use a sensitive feature.
        2. The bank knows the user's national ID (they're its customer).
        3. The bank computes SHA-256(national_id) and sends it to Waqa
           along with its own customer reference (external_user_ref).
        4. Waqa hashes once more with its pepper, finds the AccountUser,
           and creates the OrganizationUser binding.

    After linking, the bank can call /verification/sessions/create/ using
    external_user_ref to verify operations on that user.

    The organization comes from request.organization (API key) — never
    from request data.
    """

    authentication_classes = [OrganizationAPIKeyAuthentication]
    permission_classes = [HasOrganizationAPIKey, HasScope]
    required_scope = OrganizationApiKey.SCOPE_SESSION_CREATE

    def post(self, request):
        serializer = LinkUserSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        # Apply Waqa's pepper to the SHA-256 the bank sent us.
        national_id_hmac = hash_national_id_storage(data["national_id_hash"])

        # Look up the Waqa AccountUser by its stored hash.
        try:
            account = AccountUser.objects.get(
                national_id_hmac=national_id_hmac,
                status=AccountUser.STATUS_ACTIVE,
            )
        except AccountUser.DoesNotExist:
            return Response(
                {
                    "detail": (
                        "No active Waqa account is registered with this "
                        "national ID. The user must register with Waqa first."
                    ),
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        # Create the binding. Unique constraints on OrganizationUser handle
        # duplicates atomically.
        try:
            link = OrganizationUser.objects.create(
                organization=request.organization,
                user=account,
                linked_by=(
                    request.api_key.created_by
                    if request.api_key.created_by
                    else None
                ),
                external_provider=data["external_provider"],
                external_user_ref=data["external_user_ref"],
                role=data["role"],
            )
        except IntegrityError:
            return Response(
                {
                    "detail": (
                        "This Waqa account is already linked to your "
                        "organization, or this external_user_ref is "
                        "already in use."
                    ),
                },
                status=status.HTTP_409_CONFLICT,
            )

        return Response(
            OrganizationUserSerializer(link).data,
            status=status.HTTP_201_CREATED,
        )


# ============================================================
# List linked accounts (audit)
# ============================================================
class OrganizationUserListView(APIView):
    """GET /api/organization/links/list/ — list users linked to the calling org."""

    authentication_classes = [OrganizationAPIKeyAuthentication]
    permission_classes = [HasOrganizationAPIKey, HasScope]
    required_scope = OrganizationApiKey.SCOPE_AUDIT_READ

    def get(self, request):
        links = (
            OrganizationUser.objects
            .filter(organization=request.organization)
            .select_related("user", "organization")
            .order_by("-created_at")
        )
        return Response({
            "count": links.count(),
            "links": OrganizationUserSerializer(links, many=True).data,
        })
    # ============================================================
# Pending links — for mobile app to auto-generate passkeys
# ============================================================
class MyPendingLinksView(APIView):
    """GET /api/organization/my-pending-links/"""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user

        # Get the user's active device
        device = Device.objects.filter(user=user, is_active=True).first()
        if device is None:
            return Response(
                {"detail": "No active device for this user."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Get all orgs this user is linked to
        links = (
            OrganizationUser.objects
            .filter(user=user, status=OrganizationUser.STATUS_LINKED)
            .select_related("organization")
        )

        # Filter to those WITHOUT an active passkey on this device
        pending = []
        for link in links:
            has_key = DeviceKey.objects.filter(
                device=device,
                organization=link.organization,
                key_purpose=DeviceKey.PURPOSE_AUTH,
                is_active=True,
            ).exists()

            if not has_key:
                pending.append({
                    "organization_id": str(link.organization.id),
                    "organization_name": link.organization.name,
                    "linked_at": link.created_at.isoformat(),
                    "external_user_ref": link.external_user_ref,
                })

        return Response({
            "device_id": str(device.id),
            "pending_count": len(pending),
            "pending_links": pending,
        })