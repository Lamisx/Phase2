import base64
from django.db import IntegrityError
from django.shortcuts import get_object_or_404
from rest_framework import status, generics, permissions, serializers as drf_serializers
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from rest_framework.throttling import ScopedRateThrottle
from organization_endpoints.models import OrganizationUser
from .authentication import OrganizationAPIKeyAuthentication
from .models import (
    VerificationSession,
    AuditLog,
    KeyUsageLog,
)
from .serializers import (
    CreateSessionSerializer,
    SessionStatusSerializer,
    VerificationChallengeSerializer,
    AuditLogSerializer,
    KeyUsageLogSerializer,
)
from . import services

# ============================================================
# Permissions & pagination
# ============================================================
class IsOrganizationRequest(permissions.BasePermission):
    def has_permission(self, request, view):
        return getattr(request, "organization", None) is not None
class DefaultPagination(PageNumberPagination):
    page_size = 25
    page_size_query_param = "page_size"
    max_page_size = 100

class OrgScopedThrottle(ScopedRateThrottle):
    """Per-organization throttling (auth'd requests)."""
    def get_cache_key(self, request, view):
        org = getattr(request, "organization", None)
        if org is None:
            return None
        return self.cache_format % {
            "scope": self.scope,
            "ident": str(org.id),
        }

# ============================================================
# 1. Create Session + Issue Challenge
#    POST /api/verification/sessions/create/
# ============================================================
class CreateSessionAndChallengeView(APIView):

    authentication_classes = [OrganizationAPIKeyAuthentication]
    permission_classes = [IsOrganizationRequest]
    throttle_classes = [OrgScopedThrottle]
    throttle_scope = "verify_create"
    def post(self, request):
        # device_id is optional at this stage; the device identifies itself at /verify/.
        class _Input(CreateSessionSerializer):
            device_id = drf_serializers.UUIDField(
                required=False, write_only=True, allow_null=True
            )
        serializer = _Input(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        organization = request.organization
        client_ip = services.get_client_ip(request)
        user_agent = services.get_user_agent(request)
        org_user = (
            OrganizationUser.objects
            .select_related("waqa_user")
            .filter(
                organization=organization,
                external_user_ref=data["external_user_ref"],
            )
            .first()
        )
        if org_user is None:
            services.write_audit(
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
        try:
            session, challenge = services.create_session_and_issue_challenge(
                organization=organization,
                org_user=org_user,
                org_operation_ref=data["org_operation_ref"],
                operation_type=data["operation_type"],
                client_ip=client_ip,
                user_agent=user_agent,
            )
        except IntegrityError:
            services.write_audit(
                organization_id=organization.id,
                actor_type=AuditLog.ActorType.ORG,
                actor_id=organization.id,
                action="create_session",
                result=AuditLog.Result.FAIL,
                ip_address=client_ip,
                user_agent=user_agent,
                metadata={
                    "reason": "duplicate_org_operation_ref",
                    "org_operation_ref": data["org_operation_ref"],
                },
            )
            return Response(
                {"detail": "A session with this operation reference already exists."},
                status=status.HTTP_409_CONFLICT,
            )
        services.write_audit(
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
    authentication_classes = []
    permission_classes = [permissions.AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "verify_signature"
    class _Input(drf_serializers.Serializer):
        device_id = drf_serializers.UUIDField()
        signature = drf_serializers.CharField(max_length=4096, trim_whitespace=True)

        def validate_signature(self, value):
            value = value.strip()
            if not value:
                raise drf_serializers.ValidationError("Signature is required")
            try:
                base64.b64decode(value, validate=True)
            except Exception:
                raise drf_serializers.ValidationError("Invalid signature format")
            return value
    def post(self, request, session_id):
        serializer = self._Input(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        client_ip = services.get_client_ip(request)
        user_agent = services.get_user_agent(request)

        try:
            session, decision_token = services.verify_signature_and_decide(
                session_id=session_id,
                device_id=data["device_id"],
                signature_b64=data["signature"],
            )
        except ValueError as e:
            reason = str(e)
            services.write_audit(
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
        services.write_audit(
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
                "decision_token": decision_token,  # null if denied
            },
            status=status.HTTP_200_OK,
        )

# ============================================================
# 3. Verify Decision Token (org confirms a token later)
#    POST /api/verification/sessions/<id>/verify-token/
# ============================================================
class VerifyDecisionTokenView(APIView):
    authentication_classes = [OrganizationAPIKeyAuthentication]
    permission_classes = [IsOrganizationRequest]
    throttle_classes = [OrgScopedThrottle]
    throttle_scope = "verify_read"

    def post(self, request, session_id):
        token = (request.data.get("decision_token") or "").strip()
        if not token:
            return Response(
                {"detail": "decision_token is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        ok = services.verify_decision_token(
            organization=request.organization,
            session_id=session_id,
            token=token,
        )
        services.write_audit(
            organization_id=request.organization.id,
            session_id=session_id,
            actor_type=AuditLog.ActorType.ORG,
            actor_id=request.organization.id,
            action="verify_decision_token",
            result=AuditLog.Result.OK if ok else AuditLog.Result.FAIL,
            ip_address=services.get_client_ip(request),
            user_agent=services.get_user_agent(request),
        )
        if not ok:
            return Response(
                {"valid": False, "detail": "Invalid or expired decision token."},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        return Response({"valid": True}, status=status.HTTP_200_OK)

# ============================================================
# 4. Session Status (poll)
#    GET /api/verification/sessions/<id>/status/
# ============================================================
class SessionStatusView(APIView):
    authentication_classes = [OrganizationAPIKeyAuthentication]
    permission_classes = [IsOrganizationRequest]
    throttle_classes = [OrgScopedThrottle]
    throttle_scope = "verify_read"

    def get(self, request, session_id):
        session = get_object_or_404(
            VerificationSession,
            id=session_id,
            organization=request.organization,
        )
        session.update_expired_status()
        return Response(SessionStatusSerializer(session).data)
    
# ============================================================
# 5. Cancel Session
#    POST /api/verification/sessions/<id>/cancel/
# ============================================================
class CancelSessionView(APIView):
    authentication_classes = [OrganizationAPIKeyAuthentication]
    permission_classes = [IsOrganizationRequest]
    def post(self, request, session_id):
        client_ip = services.get_client_ip(request)
        user_agent = services.get_user_agent(request)

        session = get_object_or_404(
            VerificationSession,
            id=session_id,
            organization=request.organization,
        )

        if not services.cancel_session(session):
            return Response(
                {"detail": "Session is already in a final state."},
                status=status.HTTP_409_CONFLICT,
            )
        services.write_audit(
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
# 6. List Sessions (org dashboard)
#    GET /api/verification/sessions/
# ============================================================
class ListSessionsView(generics.ListAPIView):
    authentication_classes = [OrganizationAPIKeyAuthentication]
    permission_classes = [IsOrganizationRequest]
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
# 7. List Challenges for a session (forensics)
#    GET /api/verification/sessions/<id>/challenges/
# ============================================================
class ListSessionChallengesView(generics.ListAPIView):
    authentication_classes = [OrganizationAPIKeyAuthentication]
    permission_classes = [IsOrganizationRequest]
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
    permission_classes = [IsOrganizationRequest]
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
    permission_classes = [IsOrganizationRequest]
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
        return qs.order_by("-created_at")