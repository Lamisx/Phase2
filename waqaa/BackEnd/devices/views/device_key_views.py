from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone


from ..models import Device, DeviceKey,Organization
from ..serializers import DeviceKeyCreateSerializer,RegisterDeviceKeySerializer,DeviceKeySerializer


    
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