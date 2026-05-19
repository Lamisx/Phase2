"""
Device endpoints — thin wrappers around the service layer.

All endpoints require an authenticated AccountUser (JWT). The user is
taken from request.user; never from request data.

Views are intentionally minimal: they handle input parsing, call the
service, and serialize the response. All business logic lives in
services.py.
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from core.utils import get_client_ip, get_user_agent

from .serializers import (
    DeviceCreateSerializer,
    DeviceKeySerializer,
    DeviceSerializer,
    RegisterDeviceKeySerializer,
)
from .services import AccessDecisionService, DeviceKeyService, DeviceService


# ============================================================
# Device APIs
# ============================================================
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_device(request):
    """Register a new device for the authenticated user.

    Idempotent on app_instance_id: if the same instance already has
    an active device, returns the existing one with 409.
    """
    serializer = DeviceCreateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data

    # Idempotency: if this app_instance is already registered, hand it back.
    existing = DeviceService.find_existing_active_device(
        user=request.user,
        app_instance_id=data.get("app_instance_id"),
    )
    if existing:
        return Response(
            {
                "error": "DEVICE_ALREADY_REGISTERED",
                "device_id": str(existing.id),
            },
            status=status.HTTP_409_CONFLICT,
        )

    device = DeviceService.create_device(
        user=request.user,
        platform=data["platform"],
        label=data.get("label") or None,
        app_instance_id=data.get("app_instance_id"),
    )

    return Response(
        {
            "message": "DEVICE_CREATED",
            "device": DeviceSerializer(device).data,
        },
        status=status.HTTP_201_CREATED,
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def list_my_devices(request):
    """List active devices belonging to the authenticated user."""
    devices = DeviceService.list_user_devices(user=request.user)
    serializer = DeviceSerializer(devices, many=True)
    return Response(
        {"count": len(serializer.data), "devices": serializer.data},
        status=status.HTTP_200_OK,
    )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def revoke_device(request, device_id):
    """Revoke a device owned by the authenticated user."""
    device = DeviceService.revoke_device(
        device_id=device_id,
        user=request.user,
        reason=request.data.get("reason"),
    )
    return Response(
        {"message": "DEVICE_REVOKED", "device_id": str(device.id)},
        status=status.HTTP_200_OK,
    )


# ============================================================
# Device Key APIs
# ============================================================
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def register_device_key(request):
    """Register a new public key for a (device, organization, purpose) scope."""
    serializer = RegisterDeviceKeySerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data

    device_key = DeviceKeyService.register_key(
        user=request.user,
        device_id=data["device_id"],
        organization_id=data["organization_id"],
        public_key=data["public_key"],
        algorithm="ES256",
        key_format="X509",
        key_purpose=data["key_purpose"],
    )

    return Response(
        {
            "message": "DEVICE_KEY_REGISTERED",
            "device_key_id": str(device_key.id),
        },
        status=status.HTTP_201_CREATED,
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def list_device_keys(request, device_id):
    """List active keys for one of the caller's devices."""
    keys = DeviceKeyService.list_device_keys(
        user=request.user,
        device_id=device_id,
    )
    serializer = DeviceKeySerializer(keys, many=True)
    return Response(
        {"count": len(serializer.data), "keys": serializer.data},
        status=status.HTTP_200_OK,
    )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def revoke_device_key(request, device_key_id):
    """Revoke a single device key without revoking the whole device."""
    device_key = DeviceKeyService.revoke_key(
        user=request.user,
        device_key_id=device_key_id,
        reason=request.data.get("reason"),
    )
    return Response(
        {"message": "DEVICE_KEY_REVOKED", "device_key_id": str(device_key.id)},
        status=status.HTTP_200_OK,
    )


# ============================================================
# Access Decision
# ============================================================
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def access_decision(request):
    """Quick yes/no check: does the caller's device have an active key
    for the given organization?"""
    device_id = request.data.get("device_id")
    organization_id = request.data.get("organization_id")

    if not device_id:
        return Response(
            {"error": "DEVICE_ID_REQUIRED"},
            status=status.HTTP_400_BAD_REQUEST,
        )
    if not organization_id:
        return Response(
            {"error": "ORGANIZATION_ID_REQUIRED"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    result = AccessDecisionService.evaluate(
        user=request.user,
        device_id=device_id,
        organization_id=organization_id,
    )

    if result == AccessDecisionService.GRANTED:
        return Response({"access": "granted"}, status=status.HTTP_200_OK)

    if result == AccessDecisionService.DENIED:
        return Response({"access": "denied"}, status=status.HTTP_403_FORBIDDEN)

    # UNKNOWN_DEVICE
    return Response(
        {
            "access": "unknown_device",
            "ip": get_client_ip(request),
            "user_agent": get_user_agent(request),
        },
        status=status.HTTP_404_NOT_FOUND,
    )