from rest_framework import serializers
from .models import AuditLog, Device, DeviceKey, DeviceRevocationLog
from waqaa.BackEnd.accounts_endpoints.serializers import UserSerializer
from waqaa.BackEnd.organization_endpoints.serializers import OrganizationSerializer, OrganizationUserSerializer

# ============================================================
# Device Serializers
# ============================================================
class DeviceCreateSerializer(serializers.Serializer):

    user_id = serializers.UUIDField(required=True)
    label = serializers.CharField(required=False, allow_blank=True)
    platform = serializers.CharField(required=True)
    app_instance_id = serializers.CharField(required=False, allow_blank=True)

class DeviceSerializer(serializers.ModelSerializer):
    user_detail = UserSerializer(source='user', read_only=True)

    class Meta:
        model = Device
        fields = [
            "id",
            "label",
            "platform",
            "app_instance_id",
            "is_active",
            "created_at"
        ]



# ============================================================
# DeviceKey Serializers
# ============================================================
class DeviceKeySerializer(serializers.ModelSerializer):
    # Nested لتحسين تجربة الـ Frontend
    device_detail = DeviceSerializer(source='device', read_only=True)
    organization_detail = OrganizationSerializer(source='organization', read_only=True)

    class Meta:
        model = DeviceKey
        fields = [
            "id",
            "organization",
            "organization_detail",
            "device",
            "device_detail",
            "key_purpose",
            "algorithm",
            "key_format",
            "public_key",           
            "attestation_type",
            "attestation_data",
            "is_active",
            "last_used_at",
            "revoked_at",
            "revocation_reason",
            "created_at",
        ]
        read_only_fields = [
            'id',
            'created_at',
            'last_used_at',
            'revoked_at',
            'revocation_reason',
            'attestation_type',
            'attestation_data',
        ]

"""لإنشاء مفتاح جهاز جديد (من طرف المنظمة)"""
class DeviceKeyCreateSerializer(serializers.Serializer):
   
    organization_id = serializers.UUIDField()
    public_key = serializers.CharField()
    algorithm = serializers.ChoiceField(choices=["Ed25519"])
    key_format = serializers.ChoiceField(choices=["RAW"])
    key_purpose = serializers.ChoiceField(choices=["auth"])

"""لربط مفتاح جهاز موجود (من طرف الجهاز نفسه)"""
class RegisterDeviceKeySerializer(serializers.Serializer):
    
    device_id = serializers.UUIDField()
    organization_id = serializers.UUIDField()
    public_key = serializers.CharField()
    algorithm = serializers.ChoiceField(choices=["Ed25519"])
    key_format = serializers.ChoiceField(choices=["RAW"])
 

class DeviceRevocationLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeviceRevocationLog
        fields = '__all__'

