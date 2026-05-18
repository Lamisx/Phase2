
from django.db import IntegrityError
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
 
from accounts_endpoints.models import AccountUser
 
from .authentication import OrganizationAPIKeyAuthentication
from .models import OrganizationApiKey, OrganizationUser
from .permissions import HasOrganizationAPIKey, HasScope
from .serializers import (
    LinkUserSerializer,
    OrganizationApiKeySerializer,
    OrganizationSerializer,
    OrganizationUserSerializer,
)
 
 
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
    """GET /api/organization/api-keys/ — list keys for the calling org.
 
    Requires the audit:read scope. Creation/revocation is intentionally
    NOT exposed here — those flow through services that handle secret
    generation, hashing, and audit logging.
    """
 
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
# Link an AccountUser to the organization
# ============================================================
class LinkUserView(APIView):
    """POST /api/organization/links/ — link an AccountUser to the calling org."""
 
    authentication_classes = [OrganizationAPIKeyAuthentication]
    permission_classes = [HasOrganizationAPIKey, HasScope]
    required_scope = OrganizationApiKey.SCOPE_SESSION_CREATE
 
    def post(self, request):
        serializer = LinkUserSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
 
        # Ensure the AccountUser exists and is active.
        try:
            account = AccountUser.objects.get(
                id=data["user_id"],
                status=AccountUser.STATUS_ACTIVE,
            )
        except AccountUser.DoesNotExist:
            return Response(
                {"detail": "Account not found or not active."},
                status=status.HTTP_404_NOT_FOUND,
            )
 
        # Try to create the link. Rely on the unique_together constraints
        # to catch duplicates atomically.
        try:
            link = OrganizationUser.objects.create(
                organization=request.organization,
                user=account,
                linked_by=request.api_key.created_by,
                external_provider=data["external_provider"],
                external_user_ref=data["external_user_ref"],
                role=data["role"],
            )
        except IntegrityError:
            return Response(
                {
                    "detail": (
                        "Account is already linked to this organization or "
                        "external_user_ref is already in use."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
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