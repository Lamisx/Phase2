from django.db import IntegrityError
from django.db import transaction
from django.utils import timezone

from rest_framework import status
from rest_framework.decorators import (
    api_view,
    permission_classes,
)
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import (
    Device,
    DeviceKey,
    DeviceRevocationLog,
)

from .serializers import (
    DeviceCreateSerializer,
    DeviceKeySerializer,
    DeviceSerializer,
    RegisterDeviceKeySerializer,
)

from organization_endpoints.models import Organization

from core.utils import (
    get_client_ip,
    get_user_agent,
)


# ============================================================
# Helpers
# ============================================================

def _is_user_active(user) -> bool:
    """
    Keep compatibility with current account implementation.
    """

    if hasattr(user, "is_active"):
        return bool(user.is_active)

    return True


def _log_device_revocation(
    *,
    device,
    actor_type,
    actor_id=None,
    reason=None,
):
    DeviceRevocationLog.objects.create(
        device_id=device.id,
        user_id=device.user_id,
        revoked_by_actor_type=actor_type,
        revoked_by_actor_id=actor_id,
        reason=reason,
    )


# ============================================================
# Device APIs
# ============================================================

@api_view(["POST"])
@permission_classes([IsAuthenticated])
@transaction.atomic
def create_device(request):

    if not _is_user_active(request.user):
        return Response(
            {"error": "ACCOUNT_INACTIVE"},
            status=status.HTTP_403_FORBIDDEN,
        )

    serializer = DeviceCreateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    app_instance_id = serializer.validated_data.get(
        "app_instance_id"
    )

    existing_device = None

    if app_instance_id:
        existing_device = Device.objects.filter(
            user=request.user,
            app_instance_id=app_instance_id,
            is_active=True,
        ).first()

    if existing_device:
        return Response(
            {
                "error": "DEVICE_ALREADY_REGISTERED",
                "device_id": str(existing_device.id),
            },
            status=status.HTTP_409_CONFLICT,
        )

    has_primary = Device.objects.filter(
        user=request.user,
        is_primary_device=True,
        is_active=True,
    ).exists()

    try:
        device = Device.objects.create(
            user=request.user,
            label=serializer.validated_data.get("label"),
            platform=serializer.validated_data["platform"],
            app_instance_id=app_instance_id,
            is_primary_device=not has_primary,
        )

    except IntegrityError:
        return Response(
            {"error": "PRIMARY_DEVICE_CONFLICT"},
            status=status.HTTP_409_CONFLICT,
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

    devices = (
        Device.objects
        .filter(
            user=request.user,
            is_active=True,
        )
        .order_by("-created_at")
    )

    serializer = DeviceSerializer(
        devices,
        many=True,
    )

    return Response(
        {
            "count": len(serializer.data),
            "devices": serializer.data,
        },
        status=status.HTTP_200_OK,
    )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@transaction.atomic
def revoke_device(request, device_id):

    try:
        device = (
            Device.objects
            .select_for_update()
            .get(
                id=device_id,
                user=request.user,
            )
        )

    except Device.DoesNotExist:
        return Response(
            {"error": "DEVICE_NOT_FOUND"},
            status=status.HTTP_404_NOT_FOUND,
        )

    if not device.is_active:
        return Response(
            {"error": "DEVICE_ALREADY_REVOKED"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if device.is_primary_device:

        replacement_device = (
            Device.objects
            .filter(
                user=request.user,
                is_active=True,
                is_primary_device=False,
            )
            .exclude(id=device.id)
            .order_by("created_at")
            .first()
        )

        if replacement_device:
            replacement_device.is_primary_device = True
            replacement_device.save(
                update_fields=["is_primary_device"]
            )

    device.is_active = False
    device.is_primary_device = False

    device.save(
        update_fields=[
            "is_active",
            "is_primary_device",
            "updated_at",
        ]
    )

    DeviceKey.objects.filter(
        device=device,
        is_active=True,
    ).update(
        is_active=False,
        revoked_at=timezone.now(),
        revocation_reason="device_revoked",
    )

    _log_device_revocation(
        device=device,
        actor_type="user",
        actor_id=request.user.id,
        reason=request.data.get(
            "reason",
            "device_revoked",
        ),
    )

    return Response(
        {
            "message": "DEVICE_REVOKED",
            "device_id": str(device.id),
        },
        status=status.HTTP_200_OK,
    )


# ============================================================
# Device Key APIs
# ============================================================

@api_view(["POST"])
@permission_classes([IsAuthenticated])
@transaction.atomic
def register_device_key(request):

    serializer = RegisterDeviceKeySerializer(
        data=request.data
    )

    serializer.is_valid(raise_exception=True)

    try:
        device = Device.objects.select_for_update().get(
            id=serializer.validated_data["device_id"],
            user=request.user,
            is_active=True,
        )

    except Device.DoesNotExist:
        return Response(
            {"error": "DEVICE_NOT_FOUND"},
            status=status.HTTP_404_NOT_FOUND,
        )

    try:
        organization = Organization.objects.get(
            id=serializer.validated_data["organization_id"]
        )

    except Organization.DoesNotExist:
        return Response(
            {"error": "ORG_NOT_FOUND"},
            status=status.HTTP_404_NOT_FOUND,
        )

    # TODO:
    # verification module integration should validate
    # cryptographic attestation before trusting device keys.

    DeviceKey.objects.filter(
        device=device,
        organization=organization,
        key_purpose="auth",
        is_active=True,
    ).update(
        is_active=False,
        revoked_at=timezone.now(),
        revocation_reason="key_rotated",
    )

    device_key = DeviceKey.objects.create(
        device=device,
        organization=organization,
        key_purpose="auth",
        algorithm=serializer.validated_data["algorithm"],
        key_format=serializer.validated_data["key_format"],
        public_key=serializer.validated_data["public_key"],
        is_active=True,
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

    try:
        device = Device.objects.get(
            id=device_id,
            user=request.user,
            is_active=True,
        )

    except Device.DoesNotExist:
        return Response(
            {"error": "DEVICE_NOT_FOUND"},
            status=status.HTTP_404_NOT_FOUND,
        )

    keys = (
        DeviceKey.objects
        .filter(
            device=device,
            is_active=True,
        )
        .select_related("organization")
        .order_by("-created_at")
    )

    serializer = DeviceKeySerializer(
        keys,
        many=True,
    )

    return Response(
        {
            "count": len(serializer.data),
            "keys": serializer.data,
        },
        status=status.HTTP_200_OK,
    )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@transaction.atomic
def revoke_device_key(request, device_key_id):

    try:
        device_key = (
            DeviceKey.objects
            .select_related("device")
            .get(
                id=device_key_id,
                device__user=request.user,
            )
        )

    except DeviceKey.DoesNotExist:
        return Response(
            {"error": "DEVICE_KEY_NOT_FOUND"},
            status=status.HTTP_404_NOT_FOUND,
        )

    if not device_key.is_active:
        return Response(
            {"error": "DEVICE_KEY_ALREADY_REVOKED"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    device_key.is_active = False
    device_key.revoked_at = timezone.now()

    device_key.revocation_reason = request.data.get(
        "reason",
        "revoked_by_api",
    )

    device_key.save(
        update_fields=[
            "is_active",
            "revoked_at",
            "revocation_reason",
        ]
    )

    return Response(
        {
            "message": "DEVICE_KEY_REVOKED",
            "device_key_id": str(device_key.id),
        },
        status=status.HTTP_200_OK,
    )


# ============================================================
# Access Decision
# ============================================================

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def access_decision(request):

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

    try:
        device = Device.objects.get(
            id=device_id,
            user=request.user,
            is_active=True,
        )

    except Device.DoesNotExist:

        return Response(
            {
                "access": "unknown_device",
                "ip": get_client_ip(request),
                "user_agent": get_user_agent(request),
            },
            status=status.HTTP_404_NOT_FOUND,
        )

    has_valid_key = DeviceKey.objects.filter(
        device=device,
        organization_id=organization_id,
        is_active=True,
    ).exists()

    if has_valid_key:
        return Response(
            {"access": "granted"},
            status=status.HTTP_200_OK,
        )

    return Response(
        {"access": "denied"},
        status=status.HTTP_403_FORBIDDEN,
    )