# FULL corrected file

from rest_framework import serializers

from .models import (
    Device,
    DeviceKey,
    DeviceRevocationLog,
)

from accounts_endpoints.serializers import UserSerializer
from organization_endpoints.serializers import OrganizationSerializer


# ============================================================
# Device Create Serializer
# ============================================================

class DeviceCreateSerializer(serializers.Serializer):

    # user_id intentionally removed
    # authenticated user is taken securely from request.user

    label = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=100,
    )

    platform = serializers.ChoiceField(
        choices=[
            "android",
            "ios",
            "web",
            "desktop",
        ],
        required=True,
    )

    app_instance_id = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=100,
    )

    def validate_app_instance_id(self, value):

        value = value.strip()

        if not value:
            return None

        return value


# ============================================================
# Device Serializer
# ============================================================

class DeviceSerializer(serializers.ModelSerializer):

    # nested user details
    # useful for frontend/admin panels

    user_detail = UserSerializer(
        source="user",
        read_only=True,
    )

    class Meta:

        model = Device

        fields = [
            "id",
            "user_detail",
            "label",
            "platform",
            "app_instance_id",
            "is_primary_device",
            "is_active",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "is_primary_device",
            "is_active",
            "created_at",
            "updated_at",
        ]


# ============================================================
# Device Key Serializer
# ============================================================

class DeviceKeySerializer(serializers.ModelSerializer):

    # nested serializers improve frontend UX
    # and reduce additional API requests

    device_detail = DeviceSerializer(
        source="device",
        read_only=True,
    )

    organization_detail = OrganizationSerializer(
        source="organization",
        read_only=True,
    )

    class Meta:

        model = DeviceKey

        fields = [
            "id",

            # organization
            "organization",
            "organization_detail",

            # device
            "device",
            "device_detail",

            # key metadata
            "key_purpose",
            "algorithm",
            "key_format",

            # intentionally hidden:
            # public_key
            # attestation_data

            "attestation_type",

            # state
            "is_active",
            "last_used_at",
            "revoked_at",
            "revocation_reason",

            # timestamps
            "created_at",
        ]

        read_only_fields = [
            "id",
            "created_at",
            "last_used_at",
            "revoked_at",
            "revocation_reason",
            "attestation_type",
        ]


# ============================================================
# Register Device Key Serializer
# ============================================================

class RegisterDeviceKeySerializer(serializers.Serializer):

    device_id = serializers.UUIDField()

    organization_id = serializers.UUIDField()

    public_key = serializers.CharField()

    algorithm = serializers.ChoiceField(
        choices=["Ed25519"]
    )

    key_format = serializers.ChoiceField(
        choices=["RAW"]
    )

    key_purpose = serializers.ChoiceField(
        choices=["auth", "approval"]
    )

    def validate_public_key(self, value):

        value = value.strip()

        if len(value) < 20:
            raise serializers.ValidationError(
                "Invalid public key."
            )

        return value


# ============================================================
# Device Revocation Log Serializer
# ============================================================

class DeviceRevocationLogSerializer(serializers.ModelSerializer):

    class Meta:

        model = DeviceRevocationLog

        fields = [
            "id",
            "device_id",
            "user_id",
            "revoked_by_actor_type",
            "revoked_by_actor_id",
            "reason",
            "created_at",
        ]

        # audit logs should be immutable

        read_only_fields = fields