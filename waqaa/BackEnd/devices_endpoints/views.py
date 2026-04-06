import json
import secrets
from datetime import timedelta

from django.utils import timezone
from django.db import transaction

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from .models import (
    Device,
    DeviceKey,
    VerificationSession,
    VerificationChallenge,
    DeviceRevocationLog,
)

from .serializers import (
    DeviceCreateSerializer,
    DeviceSerializer,
    RegisterDeviceKeySerializer,
    DeviceKeySerializer,
    CreateSessionSerializer,
    VerifySessionSerializer,
    SessionStatusSerializer,
)

from accounts_endpoints.models import WaqaUser, DelegatedAccess
from organization_endpoints.models import Organization, OrganizationApiKey, OrganizationUser

from core.utils import hash_api_key
from core.utils_crypto import verify_ed25519_signature
    
@api_view(["POST"])
def register_device_key(request):
    serializer = RegisterDeviceKeySerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    device_id = serializer.validated_data["device_id"]
    org_id = serializer.validated_data["organization_id"]

    try:
        device = Device.objects.get(id=device_id, is_active=True)
    except Device.DoesNotExist:
        return Response({"error": "DEVICE_NOT_FOUND"}, status=404)

    try:
        organization = Organization.objects.get(id=org_id)
    except Organization.DoesNotExist:
        return Response({"error": "ORG_NOT_FOUND"}, status=404)

    # deactivate old key (same device + org)
    DeviceKey.objects.filter(
        device=device,
        organization=organization,
        key_purpose="auth",
        is_active=True
    ).update(is_active=False)

    device_key = DeviceKey.objects.create(
        device=device,
        organization=organization,
        key_purpose="auth",
        algorithm=serializer.validated_data["algorithm"],
        key_format=serializer.validated_data["key_format"],
        public_key=serializer.validated_data["public_key"],
        is_active=True
    )

    return Response({
        "message": "DEVICE_KEY_REGISTERED",
        "device_key_id": str(device_key.id)
    })

@api_view(["GET"])
def list_device_keys(request, device_id):
    try:
        device = Device.objects.get(id=device_id)
    except Device.DoesNotExist:
        return Response(
            {"error": "DEVICE_NOT_FOUND"},
            status=status.HTTP_404_NOT_FOUND
        )

    keys = DeviceKey.objects.filter(device=device).order_by("-created_at")
    serializer = DeviceKeySerializer(keys, many=True)

    return Response(
        {
            "count": len(serializer.data),
            "keys": serializer.data
        },
        status=status.HTTP_200_OK
    )



@api_view(["POST"])
def revoke_device_key(request, device_key_id):
    try:
        device_key = DeviceKey.objects.get(id=device_key_id)
    except DeviceKey.DoesNotExist:
        return Response(
            {"error": "DEVICE_KEY_NOT_FOUND"},
            status=status.HTTP_404_NOT_FOUND
        )

    if not device_key.is_active:
        return Response(
            {"error": "DEVICE_KEY_ALREADY_REVOKED"},
            status=status.HTTP_400_BAD_REQUEST
        )

    device_key.is_active = False
    device_key.revoked_at = timezone.now()
    device_key.revocation_reason = "revoked_by_api"
    device_key.save()

    return Response(
        {
            "message": "DEVICE_KEY_REVOKED",
            "device_key_id": str(device_key.id)
        },
        status=status.HTTP_200_OK
    )


#هل هنا مفترض يكون اتخاذ القرار ؟ لاني اشوف خطا يكون هنا 
@api_view(["POST"])
def access_decision(request):

    device_id = request.data.get("device_id")

    if not device_id:
        return Response({"error": "device_id required"}, status=400)

    try:
        device = Device.objects.get(id=device_id)

        if device.is_active:
            return Response({"access": "granted"})
        else:
            return Response({"access": "denied"})

    except Device.DoesNotExist:
        return Response({"access": "unknown_device"}, status=404)


@api_view(["POST"])
def create_device(request):

    serializer = DeviceCreateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    user_id = serializer.validated_data["user_id"]

    try:
        user = WaqaUser.objects.get(id=user_id)
    except WaqaUser.DoesNotExist:
        return Response(
            {"error": "User not found"},
            status=status.HTTP_404_NOT_FOUND
        )

    device = Device.objects.create(
        user=user,
        label=serializer.validated_data.get("label"),
        platform=serializer.validated_data.get("platform"),
        app_instance_id=serializer.validated_data.get("app_instance_id")
    )

    return Response(
        {
            "message": "Device created successfully",
            "device_id": str(device.id)
        },
        status=status.HTTP_201_CREATED
    )

@api_view(["GET"])
def list_devices(request, user_id):
    try:
        user = WaqaUser.objects.get(id=user_id)
    except WaqaUser.DoesNotExist:
        return Response(
            {"error": "User not found"},
            status=status.HTTP_404_NOT_FOUND
        )

    devices = Device.objects.filter(user=user).order_by("-created_at")
    serializer = DeviceSerializer(devices, many=True)

    return Response(
        {
            "count": len(serializer.data),
            "devices": serializer.data
        },
        status=status.HTTP_200_OK)

from django.db import transaction
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from .models import Device, DeviceKey, DeviceRevocationLog


@api_view(["POST"])
@transaction.atomic
def revoke_device(request, device_id):
    try:
        device = Device.objects.select_for_update().get(id=device_id)
    except Device.DoesNotExist:
        return Response(
            {"error": "DEVICE_NOT_FOUND"},
            status=status.HTTP_404_NOT_FOUND
        )

    if not device.is_active:
        return Response(
            {"error": "DEVICE_ALREADY_REVOKED"},
            status=status.HTTP_400_BAD_REQUEST
        )

    device.is_active = False
    device.save()

    DeviceKey.objects.filter(
        device=device,
        is_active=True
    ).update(
        is_active=False,
        revocation_reason="device_revoked"
    )

    DeviceRevocationLog.objects.create(
        device_id=device.id,
        user_id=device.user.id if device.user_id else None,
        revoked_by_actor_type="user",
        reason="device_revoked"
    )

    return Response(
        {
            "message": "DEVICE_REVOKED",
            "device_id": str(device.id)
        },
        status=status.HTTP_200_OK
    )



@api_view(["POST"])
def create_session(request):

    serializer = CreateSessionSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    org_key = serializer.validated_data["organization_api_key"]
    external_user_ref = serializer.validated_data["external_user_ref"]
    org_operation_ref = serializer.validated_data["org_operation_ref"]
    operation_type = serializer.validated_data["operation_type"]

    # 1️  verify organization api key
    try:
        key_hash= hash_api_key(org_key)
        api_key = OrganizationApiKey.objects.get(key_hash=key_hash, is_active=True)
    except OrganizationApiKey.DoesNotExist:
        return Response(
            {"error": "Invalid organization API key"},
            status=status.HTTP_401_UNAUTHORIZED
        )

    organization = api_key.organization

    # 2️ find user inside organization
    try:
        org_user = OrganizationUser.objects.get(
            organization=organization,
            external_user_ref=external_user_ref,# external_user_ref in session creation always refers to the primary user in the organization.
            status="linked"
        )
    except OrganizationUser.DoesNotExist:
        return Response(
            {"error": "User not found for this organization"},
            status=status.HTTP_404_NOT_FOUND
        )

    # 3️ check duplicate operation
    if VerificationSession.objects.filter(
        organization=organization,
        org_operation_ref=org_operation_ref
    ).exists():
        return Response(
            {"error": "Operation reference already exists"},
            status=status.HTTP_409_CONFLICT
        )

    # 4️ create session expiry
    expires_at = timezone.now() + timedelta(minutes=2)

    # 5️ create session
    session = VerificationSession.objects.create(
        organization=organization,
        org_user=org_user,
        org_operation_ref=org_operation_ref,
        operation_type=operation_type,
        nonce=secrets.token_hex(16),
        status="challenge_issued",
        expires_at=expires_at
    )

    # 6️ create challenge payload
    challenge_payload = {
        "session_id": str(session.id),
        "nonce": secrets.token_hex(32),
        "expires_at": expires_at.isoformat()
    }

    challenge_bytes = json.dumps(
        challenge_payload,
        sort_keys=True,
        separators=(",", ":")
    )

    # 7️ store challenge
    challenge = VerificationChallenge.objects.create(
        session=session,
        challenge_bytes=challenge_bytes,
        attempt_number=1,
        expires_at=expires_at
    )

    # 8️ response
    return Response(
        {
            "message": "Verification session created successfully",
            "session_id": str(session.id),
            "challenge": challenge_payload,
            "status": "challenge_issued",
            "expires_at": expires_at
        },
        status=status.HTTP_201_CREATED
    )

@api_view(['POST'])
@transaction.atomic
def verify_session(request, session_id):

    challenge_id = request.data.get("challenge_id")
    signature = request.data.get("signature")
    device_id = request.data.get("device_id")

    try:
        session = VerificationSession.objects.select_for_update().get(id=session_id)

        challenge = VerificationChallenge.objects.get(
            id=challenge_id,
            session=session
        )

        # 1) تحقق من انتهاء الجلسة
        if session.expires_at < timezone.now():
            return Response({"error": "SESSION_EXPIRED"}, status=400)

        # 2) تحقق من التحدي
        if not challenge.is_active or challenge.is_used:
            return Response({"error": "INVALID_CHALLENGE"}, status=400)
        
        if challenge.expires_at < timezone.now():
            return Response({"error": "CHALLENGE_EXPIRED"}, status=400)

        # 3) الجهاز
        device = Device.objects.get(id=device_id, is_active=True)

        # 4) primary vs delegate
        if device.user_id == session.org_user.user_id:
            actor_type = "primary"
        else:
            is_delegate = DelegatedAccess.objects.filter(
                primary_user_id=session.org_user.user_id,
                delegate_user_id=device.user_id,
                status='active'
            ).exists()

            if not is_delegate:
                return Response({"error": "NOT_AUTHORIZED"}, status=403)

            actor_type = "delegate"

        # 5) المفتاح
        device_key = DeviceKey.objects.get(
            device=device,
            organization=session.organization,
            is_active=True
        )

        # 6) التحقق (مؤقت)
        is_valid = verify_ed25519_signature(
            public_key_b64=device_key.public_key,
            message=challenge.challenge_bytes,
            signature_b64=signature
        )

        if is_valid:
            challenge.is_used = True
            challenge.is_active = False
            challenge.used_at = timezone.now()
            challenge.save()

            session.status = "verified"
            session.verified_at = timezone.now()
            session.device_id = device.id
            session.verified_by_user = device.user
            session.verified_by_actor_type = actor_type
            session.save()

            return Response({"status": "verified"})

        else:
            session.attempt_count += 1

            if session.attempt_count >= session.max_attempts:
                session.status = "failed"
                session.failure_reason = "max_attempts_reached"

            session.save()

            return Response({"error": "INVALID_SIGNATURE"}, status=400)

    except VerificationSession.DoesNotExist:
        return Response({"error": "SESSION_NOT_FOUND"}, status=404)

    except Exception as e:
        return Response({"error": str(e)}, status=500)
    

@api_view(["GET"])
def get_session_status(request, session_id):
    try:
        session = VerificationSession.objects.get(id=session_id)
    except VerificationSession.DoesNotExist:
        return Response(
            {"error": "SESSION_NOT_FOUND"},
            status=status.HTTP_404_NOT_FOUND
        )

    # optional: لو انتهت الجلسة ولم تحدث حالتها بعد
    if session.status in ["pending", "challenge_issued", "awaiting_user"] and session.expires_at < timezone.now():
        session.status = "expired"
        session.failure_reason = "session_expired"
        session.save()

    serializer = SessionStatusSerializer(session)

    return Response(
        {
            "session_id": str(session.id),
            "status": serializer.data["status"],
            "operation_type": serializer.data["operation_type"],
            "org_operation_ref": serializer.data["org_operation_ref"],
            "verified_at": serializer.data["verified_at"],
            "expires_at": serializer.data["expires_at"],
            "failure_reason": serializer.data["failure_reason"],
        },
        status=status.HTTP_200_OK
    )
    
@api_view(["POST"])
@transaction.atomic
def cancel_session(request, session_id):
    try:
        session = VerificationSession.objects.select_for_update().get(id=session_id)
    except VerificationSession.DoesNotExist:
        return Response(
            {"error": "SESSION_NOT_FOUND"},
            status=status.HTTP_404_NOT_FOUND
        )

    if session.status in ["verified", "failed", "expired", "cancelled", "denied"]:
        return Response(
            {"error": "SESSION_ALREADY_FINALIZED"},
            status=status.HTTP_400_BAD_REQUEST
        )

    VerificationChallenge.objects.filter(
        session=session,
        is_active=True
    ).update(is_active=False)

    session.status = "cancelled"
    session.failure_reason = "session_cancelled"
    session.save()

    return Response(
        {
            "message": "SESSION_CANCELLED",
            "session_id": str(session.id)
        },
        status=status.HTTP_200_OK
    )


