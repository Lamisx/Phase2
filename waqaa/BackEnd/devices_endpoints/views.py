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
    DeviceRevocationLog,
)

from .serializers import (
    DeviceCreateSerializer,
    DeviceSerializer,
    RegisterDeviceKeySerializer,
    DeviceKeySerializer,
    
)

from accounts_endpoints.models import WaqaUser, DelegatedAccess
from organization_endpoints.models import Organization, OrganizationApiKey, OrganizationUser

from core.utils import hash_api_key
from core.utils_crypto import verify_ed25519_signature
def create_session(request):
    return Response({"message": "Session created"})
    
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





