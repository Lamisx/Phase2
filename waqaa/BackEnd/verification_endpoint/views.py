"""
Verification endpoints.

Authentication model:
    Organization-facing endpoints  → X-API-Key header (organization_endpoints
                                     OrganizationAPIKeyAuthentication).
    Device-facing /verify/         → no auth header; the device proves itself
                                     by signing the challenge with its private
                                     key. The signature replaces a token.
"""
from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, status
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView

from core.utils import get_client_ip, get_user_agent
from organization_endpoints.authentication import OrganizationAPIKeyAuthentication
from organization_endpoints.models import OrganizationApiKey, OrganizationUser
from organization_endpoints.permissions import HasOrganizationAPIKey, HasScope

from .models import AuditLog, KeyUsageLog, VerificationSession
from .serializers import (
    AuditLogSerializer,
    CreateSessionInputSerializer,
    KeyUsageLogSerializer,
    SessionStatusSerializer,
    VerificationChallengeSerializer,
    VerifySignatureInputSerializer,
)
from .services import VerificationService, write_audit


# ============================================================
# Pagination
# ============================================================
class DefaultPagination(PageNumberPagination):
    page_size = 25
    page_size_query_param = "page_size"
    max_page_size = 100


# ============================================================
# 1. Create Session + Issue Challenge
#    POST /api/verification/sessions/create/
# ============================================================
class CreateSessionAndChallengeView(APIView):
    """Organization creates a verification session for one of its users.

    Requires scope: session:create.
    """

    authentication_classes = [OrganizationAPIKeyAuthentication]
    permission_classes = [HasOrganizationAPIKey, HasScope]
    required_scope = OrganizationApiKey.SCOPE_SESSION_CREATE

    def post(self, request):
        serializer = CreateSessionInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        organization = request.organization
        client_ip = get_client_ip(request)
        user_agent = get_user_agent(request)

        # Resolve the org-side user reference to one of our AccountUsers.
        org_user = (
            OrganizationUser.objects
            .select_related("user")
            .filter(
                organization=organization,
                external_user_ref=data["external_user_ref"],
            )
            .first()
        )
        if org_user is None:
            write_audit(
                organization_id=organization.id,
                actor_type=AuditLog.ActorType.ORG,
                actor_id=organization.id,
                action="create_session",
                result=AuditLog.Result.FAIL,
                ip_address=client_ip,
                user_agent=user_agent,
                metadata={
                    "reason": "org_user_not_found",
                    "external_user_ref": data["external_user_ref"],
                },
            )
            return Response(
                {"detail": "User reference not found for this organization."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Create session + first challenge (atomic).
        try:
            session, challenge = VerificationService.create_session_and_issue_challenge(
                organization=organization,
                org_user=org_user,
                org_operation_ref=data["org_operation_ref"],
                operation_type=data["operation_type"],
                operation_hash=data.get("operation_hash") or None,
                operation_payload_encrypted=data.get("operation_payload_encrypted") or None,
                client_ip=client_ip,
                user_agent=user_agent,
            )
        except Exception as exc:
            # The most common cause is the unique constraint on
            # (organization, org_operation_ref). We surface this as 409.
            write_audit(
                organization_id=organization.id,
                actor_type=AuditLog.ActorType.ORG,
                actor_id=organization.id,
                action="create_session",
                result=AuditLog.Result.FAIL,
                ip_address=client_ip,
                user_agent=user_agent,
                metadata={
                    "reason": "session_create_failed",
                    "error": str(exc)[:200],
                    "org_operation_ref": data["org_operation_ref"],
                },
            )
            return Response(
                {"detail": "A session with this operation reference already exists."},
                status=status.HTTP_409_CONFLICT,
            )

        write_audit(
            organization_id=organization.id,
            session_id=session.id,
            actor_type=AuditLog.ActorType.ORG,
            actor_id=organization.id,
            action="create_session",
            result=AuditLog.Result.OK,
            ip_address=client_ip,
            user_agent=user_agent,
            metadata={
                "operation_type": data["operation_type"],
                "challenge_id": str(challenge.id),
            },
        )

        return Response(
            {
                "session_id": str(session.id),
                "challenge_bytes": challenge.challenge_bytes,
                "challenge_expires_at": challenge.expires_at,
                "session_status": session.status,
                "session": SessionStatusSerializer(session).data,
            },
            status=status.HTTP_201_CREATED,
        )


# ============================================================
# 2. Verify Device Signature
#    POST /api/verification/sessions/<id>/verify/
# ============================================================
class VerifyDeviceSignatureView(APIView):
    """Device-side endpoint — the device signs the challenge and posts it.

    No auth header: the cryptographic signature IS the authentication.
    """

    authentication_classes = []
    permission_classes = [permissions.AllowAny]

    def post(self, request, session_id):
        serializer = VerifySignatureInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        client_ip = get_client_ip(request)
        user_agent = get_user_agent(request)

        try:
            session, decision_token = VerificationService.verify_signature_and_decide(
                session_id=session_id,
                device_id=data["device_id"],
                signature_b64=data["signature"],
            )
        except ValueError as exc:
            reason = str(exc)
            write_audit(
                session_id=session_id,
                device_id=data["device_id"],
                actor_type=AuditLog.ActorType.USER,
                action="verify_signature",
                result=AuditLog.Result.FAIL,
                ip_address=client_ip,
                user_agent=user_agent,
                metadata={"reason": reason},
            )
            return Response({"detail": reason}, status=status.HTTP_400_BAD_REQUEST)

        write_audit(
            organization_id=session.organization_id,
            session_id=session.id,
            device_id=data["device_id"],
            actor_type=AuditLog.ActorType.USER,
            action="verify_signature",
            result=(
                AuditLog.Result.OK
                if session.status == VerificationSession.Status.VERIFIED
                else AuditLog.Result.FAIL
            ),
            ip_address=client_ip,
            user_agent=user_agent,
            metadata={
                "session_status": session.status,
                "failure_reason": session.failure_reason,
                "actor_type": session.verified_by_actor_type,
            },
        )

        return Response(
            {
                "session": SessionStatusSerializer(session).data,
                "decision": session.status,
                "decision_token": decision_token,  # None when denied
            },
            status=status.HTTP_200_OK,
        )


# ============================================================
# 3. Verify Decision Token (organization callback)
#    POST /api/verification/sessions/<id>/verify-token/
# ============================================================
class VerifyDecisionTokenView(APIView):
    """Organization later confirms a decision_token it received from the device."""

    authentication_classes = [OrganizationAPIKeyAuthentication]
    permission_classes = [HasOrganizationAPIKey, HasScope]
    required_scope = OrganizationApiKey.SCOPE_SESSION_READ

    def post(self, request, session_id):
        token = (request.data.get("decision_token") or "").strip()
        if not token:
            return Response(
                {"detail": "decision_token is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        ok = VerificationService.verify_decision_token(
            organization=request.organization,
            session_id=session_id,
            token=token,
        )

        write_audit(
            organization_id=request.organization.id,
            session_id=session_id,
            actor_type=AuditLog.ActorType.ORG,
            actor_id=request.organization.id,
            action="verify_decision_token",
            result=AuditLog.Result.OK if ok else AuditLog.Result.FAIL,
            ip_address=get_client_ip(request),
            user_agent=get_user_agent(request),
        )

        if not ok:
            return Response(
                {"valid": False, "detail": "Invalid or expired decision token."},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        return Response({"valid": True}, status=status.HTTP_200_OK)


# ============================================================
# 4. Session Status (polling)
#    GET /api/verification/sessions/<id>/status/
# ============================================================
class SessionStatusView(APIView):
    authentication_classes = [OrganizationAPIKeyAuthentication]
    permission_classes = [HasOrganizationAPIKey, HasScope]
    required_scope = OrganizationApiKey.SCOPE_SESSION_READ

    def get(self, request, session_id):
        session = get_object_or_404(
            VerificationSession,
            id=session_id,
            organization=request.organization,
        )
        # Side-effect: lazily transition to EXPIRED if past expires_at.
        session.update_expired_status()
        return Response(SessionStatusSerializer(session).data)


# ============================================================
# 5. Cancel Session
#    POST /api/verification/sessions/<id>/cancel/
# ============================================================
class CancelSessionView(APIView):
    authentication_classes = [OrganizationAPIKeyAuthentication]
    permission_classes = [HasOrganizationAPIKey, HasScope]
    required_scope = OrganizationApiKey.SCOPE_SESSION_CANCEL

    def post(self, request, session_id):
        client_ip = get_client_ip(request)
        user_agent = get_user_agent(request)

        session = get_object_or_404(
            VerificationSession,
            id=session_id,
            organization=request.organization,
        )

        if not VerificationService.cancel_session(session=session):
            return Response(
                {"detail": "Session is already in a final state."},
                status=status.HTTP_409_CONFLICT,
            )

        write_audit(
            organization_id=request.organization.id,
            session_id=session.id,
            actor_type=AuditLog.ActorType.ORG,
            actor_id=request.organization.id,
            action="cancel_session",
            result=AuditLog.Result.OK,
            ip_address=client_ip,
            user_agent=user_agent,
        )

        return Response(SessionStatusSerializer(session).data)


# ============================================================
# 6. List Sessions (organization dashboard)
#    GET /api/verification/sessions/
# ============================================================
class ListSessionsView(generics.ListAPIView):
    authentication_classes = [OrganizationAPIKeyAuthentication]
    permission_classes = [HasOrganizationAPIKey, HasScope]
    required_scope = OrganizationApiKey.SCOPE_AUDIT_READ
    serializer_class = SessionStatusSerializer
    pagination_class = DefaultPagination

    def get_queryset(self):
        qs = VerificationSession.objects.filter(organization=self.request.organization)
        params = self.request.query_params

        if v := params.get("status"):
            qs = qs.filter(status=v)
        if v := params.get("operation_type"):
            qs = qs.filter(operation_type=v)
        if v := params.get("org_operation_ref"):
            qs = qs.filter(org_operation_ref=v)
        if v := params.get("from"):
            qs = qs.filter(created_at__gte=v)
        if v := params.get("to"):
            qs = qs.filter(created_at__lte=v)

        return qs.order_by("-created_at")


# ============================================================
# 7. List Challenges of a Session (forensics)
#    GET /api/verification/sessions/<id>/challenges/
# ============================================================
class ListSessionChallengesView(generics.ListAPIView):
    authentication_classes = [OrganizationAPIKeyAuthentication]
    permission_classes = [HasOrganizationAPIKey, HasScope]
    required_scope = OrganizationApiKey.SCOPE_AUDIT_READ
    serializer_class = VerificationChallengeSerializer
    pagination_class = DefaultPagination

    def get_queryset(self):
        session = get_object_or_404(
            VerificationSession,
            id=self.kwargs["session_id"],
            organization=self.request.organization,
        )
        return session.challenges.order_by("-attempt_number")


# ============================================================
# 8. Audit Logs
#    GET /api/verification/audit-logs/
# ============================================================
class AuditLogListView(generics.ListAPIView):
    authentication_classes = [OrganizationAPIKeyAuthentication]
    permission_classes = [HasOrganizationAPIKey, HasScope]
    required_scope = OrganizationApiKey.SCOPE_AUDIT_READ
    serializer_class = AuditLogSerializer
    pagination_class = DefaultPagination

    def get_queryset(self):
        qs = AuditLog.objects.filter(organization_id=self.request.organization.id)
        params = self.request.query_params

        if v := params.get("session_id"):
            qs = qs.filter(session_id=v)
        if v := params.get("device_id"):
            qs = qs.filter(device_id=v)
        if v := params.get("action"):
            qs = qs.filter(action=v)
        if v := params.get("result"):
            qs = qs.filter(result=v)
        if v := params.get("actor_type"):
            qs = qs.filter(actor_type=v)
        if v := params.get("from"):
            qs = qs.filter(created_at__gte=v)
        if v := params.get("to"):
            qs = qs.filter(created_at__lte=v)

        return qs.order_by("-created_at")


# ============================================================
# 9. Key Usage Logs
#    GET /api/verification/key-usage-logs/
# ============================================================
class KeyUsageLogListView(generics.ListAPIView):
    authentication_classes = [OrganizationAPIKeyAuthentication]
    permission_classes = [HasOrganizationAPIKey, HasScope]
    required_scope = OrganizationApiKey.SCOPE_AUDIT_READ
    serializer_class = KeyUsageLogSerializer
    pagination_class = DefaultPagination

    def get_queryset(self):
        qs = KeyUsageLog.objects.filter(organization_id=self.request.organization.id)
        params = self.request.query_params

        if v := params.get("session_id"):
            qs = qs.filter(session_id=v)
        if v := params.get("device_id"):
            qs = qs.filter(device_id=v)
        if v := params.get("action"):
            qs = qs.filter(action=v)
        if v := params.get("result"):
            qs = qs.filter(result=v)
        if v := params.get("from"):
            qs = qs.filter(created_at__gte=v)
        if v := params.get("to"):
            qs = qs.filter(created_at__lte=v)

        return qs.order_by("-created_at")