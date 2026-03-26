from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from ..models import Device, WaqaUser,Organization,DeviceKey
from ..serializers import DeviceCreateSerializer, DeviceSerializer,RegisterDeviceKeySerializer


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

from ..models import Device, DeviceKey, DeviceRevocationLog


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
