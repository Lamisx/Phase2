from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
 
from .serializers import (
    AccountSerializer,
    CompleteRegistrationSerializer,
    CreateDelegationSerializer,
    DelegationSerializer,
    LoginSerializer,
    StartRegistrationSerializer,
)
from .services import DelegationService, RegistrationService
 
 
# ============================================================
# Health
# ============================================================
@api_view(["GET"])
@permission_classes([AllowAny])
def health_check(request):
    return Response({"status": "ok"})
 
 
# ============================================================
# Registration flow
# ============================================================
@api_view(["POST"])
@permission_classes([AllowAny])
def start_registration(request):

    serializer = StartRegistrationSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
 
    session = RegistrationService.start_registration(
        national_id=serializer.validated_data["national_id"],
    )
 
    return Response(
        {
            "session_id": str(session.id),
            "status": session.status,
            "expires_at": session.expires_at,
        },
        status=status.HTTP_201_CREATED,
    )
 
 
@api_view(["POST"])
@permission_classes([AllowAny])
def verify_identity(request):

    session_id = request.data.get("session_id")
    if not session_id:
        return Response(
            {"detail": "session_id is required."},
            status=status.HTTP_400_BAD_REQUEST,
        )
 
    session = RegistrationService.mark_identity_verified(session_id=session_id)
    return Response(
        {"session_id": str(session.id), "status": session.status},
        status=status.HTTP_200_OK,
    )
 
 
@api_view(["POST"])
@permission_classes([AllowAny])
def complete_registration(request):

    serializer = CompleteRegistrationSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data
 
    session, account = RegistrationService.complete_registration(
        session_id=data["session_id"],
        username=data["username"],
        display_name=data["display_name"],
        password=data["password"],
        phone=data["phone"],
        email=data.get("email"),
    )
 
    refresh = RefreshToken.for_user(account)
 
    return Response(
        {
            "message": "Account created.",
            "user": AccountSerializer(account).data,
            "tokens": {
                "access": str(refresh.access_token),
                "refresh": str(refresh),
            },
        },
        status=status.HTTP_201_CREATED,
    )
 
 
# ============================================================
# Login (issues JWT)
# ============================================================
@api_view(["POST"])
@permission_classes([AllowAny])
def login(request):
    serializer = LoginSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    user = serializer.validated_data["user"]
 
    refresh = RefreshToken.for_user(user)
 
    return Response(
        {
            "message": "Login successful.",
            "user": AccountSerializer(user).data,
            "tokens": {
                "access": str(refresh.access_token),
                "refresh": str(refresh),
            },
        },
        status=status.HTTP_200_OK,
    )
 
 
# ============================================================
# "Me" — current user info
# ============================================================
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def me(request):
    return Response(AccountSerializer(request.user).data)
 
 
# ============================================================
# Delegation endpoints
# ============================================================

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_delegation(request):

    serializer = CreateDelegationSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data
 
    delegation = DelegationService.create_delegation(
        owner=request.user,                              
        delegated_account_id=data["delegated_account_id"],
        delegation_method=data["delegation_method"],
        expires_at=data.get("expires_at"),
    )
 
    return Response(
        {
            "message": "Delegation created.",
            "delegation": DelegationSerializer(delegation).data,
        },
        status=status.HTTP_201_CREATED,
    )
 
 
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def list_delegations(request):
    """GET /api/account/delegations/
 
    List delegations granted BY the authenticated user.
    """
    delegations = DelegationService.list_delegations(owner=request.user)
    serializer = DelegationSerializer(delegations, many=True)
    return Response(
        {"count": len(serializer.data), "delegations": serializer.data},
        status=status.HTTP_200_OK,
    )
 
 
@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def revoke_delegation(request, delegation_id):
    """DELETE /api/account/delegations/<id>/revoke/
 
    Revoke a delegation. The service verifies the caller is the
    owner — only the granter of a delegation can revoke it.
    """
    delegation = DelegationService.revoke_delegation(
        delegation_id=delegation_id,
        owner=request.user,                             
    )
    return Response(
        {
            "message": "Delegation revoked.",
            "delegation": DelegationSerializer(delegation).data,
        },
        status=status.HTTP_200_OK,
    )
 