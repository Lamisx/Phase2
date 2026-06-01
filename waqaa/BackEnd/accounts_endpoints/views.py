from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

import hashlib
from core.utils_crypto import hash_national_id_storage
from .models import (
    AccountUser,
    DelegationCode,
    UserDelegation,
 
) 
from .serializers import (
    AccountSerializer,
    CompleteRegistrationSerializer,
    CreateDelegationSerializer,
    DelegationSerializer,
    LoginSerializer,
    StartRegistrationSerializer,
    AcceptDelegationCodeSerializer,
)
from .services import DelegationService, RegistrationService,DelegationCodeService
 

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

    serializer = CompleteRegistrationSerializer(
        data=request.data
    )

    serializer.is_valid(raise_exception=True)

    data = serializer.validated_data

    # =========================================
    # GET NATIONAL ID
    # =========================================

    national_id = data["national_id"]

    # =========================================
    # HASH NATIONAL ID
    # =========================================


    national_id_sha256 = hashlib.sha256(
        national_id.encode("utf-8")
    ).hexdigest()

    # الخطوة 2: HMAC مع pepper وقاء
    national_id_hmac = hash_national_id_storage(
        national_id_sha256
    )

    # =========================================
    # CREATE ACCOUNT
    # =========================================

    account = AccountUser.objects.create_user(
        username=data["username"],

        display_name=data["display_name"],

        password=data["password"],

        phone=data["phone"],

        email=data.get("email"),

        # ✅ IMPORTANT
        national_id_hmac=national_id_hmac,
    )

    # =========================================
    # JWT TOKENS
    # =========================================

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
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def accept_delegation_code(request):

    serializer = AcceptDelegationCodeSerializer(
        data=request.data
    )

    serializer.is_valid(raise_exception=True)

    code = serializer.validated_data["code"]

    try:
        delegation_code = DelegationCode.objects.get(
            code=code,
            is_used=False,
        )

    except DelegationCode.DoesNotExist:

        return Response(
            {
                "detail": "Invalid code."
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    if delegation_code.is_expired:

        return Response(
            {
                "detail": "Code expired."
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    if delegation_code.owner_account == request.user:

        return Response(
            {
                "detail": "You cannot delegate to yourself."
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    delegation_code.is_used = True
    delegation_code.save(update_fields=["is_used"])

    delegation = UserDelegation.objects.create(
        owner_account=delegation_code.owner_account,
        delegated_account=request.user,
        delegation_method=UserDelegation.METHOD_OTP,
    )

    return Response(
        {
            "message": "Delegation created.",
            "delegation": DelegationSerializer(
                delegation
            ).data,
        },
        status=status.HTTP_201_CREATED,
    )
# ============================================================
# Delegation Code Views
# ============================================================


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def generate_delegation_code(request):
    """
    A يطلب رمز تفويض لإعطائه لـ B.
    Response: { code: "847291", expires_in: 300, expires_at: "..." }
    """
    dcode = DelegationCodeService.generate_for(owner=request.user)
    return Response(
        {
            "code": dcode.code,
            "expires_in": 60 * DelegationCodeService.CODE_TTL_MINUTES,
            "expires_at": dcode.expires_at.isoformat(),
        },
        status=status.HTTP_201_CREATED,
    )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def accept_delegation_code(request):
    """
    B يُدخل الرمز الذي حصل عليه من A.
    Body: { code: "847291" }
    Response: تفاصيل التفويض الناتج (UserDelegation)
    """
    serializer = AcceptDelegationCodeSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    delegation = DelegationCodeService.accept(
        code=serializer.validated_data["code"],
        delegated=request.user,
    )

    return Response(
        {
            "message": "DELEGATION_ACCEPTED",
            "delegation": DelegationSerializer(delegation).data,
        },
        status=status.HTTP_201_CREATED,
    )

# ============================================================
# ADD these two views to accounts_endpoints/views.py
#
# المكان: في نهاية الملف، بعد accept_delegation_code
# ============================================================


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def list_received_delegations(request):
    """
    GET /api/account/delegations/received/

    ترجع التفويضات اللي استلمها المستخدم الحالي.
    تُستخدم في شاشة "الحسابات المرتبطة" — B يرى من فوّضه.
    """
    delegations = DelegationService.list_received(delegated=request.user)
    serializer = DelegationSerializer(delegations, many=True)
    return Response(
        {"count": len(serializer.data), "delegations": serializer.data},
        status=status.HTTP_200_OK,
    )


@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def revoke_my_delegation(request, delegation_id):
    """
    DELETE /api/account/delegations/<id>/revoke-as-delegated/

    B يلغي تفويضه عن A (من جانب المُفوَّض).
    مختلفة عن revoke_delegation التي تتطلب أن يكون الـ caller هو owner.
    """
    delegation = DelegationService.revoke_as_delegated(
        delegation_id=delegation_id,
        delegated=request.user,
    )
    return Response(
        {
            "message": "Delegation revoked.",
            "delegation": DelegationSerializer(delegation).data,
        },
        status=status.HTTP_200_OK,
    )