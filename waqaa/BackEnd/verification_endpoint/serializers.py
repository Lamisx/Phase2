from rest_framework import serializers
from .models import AuditLog, KeyUsageLog, VerificationSession, VerificationChallenge
from organization_endpoints.models import Organization
from django.utils import timezone
from django.db import transaction
import base64


class OperationType:
    LOGIN = "login"
    UPDATE_PROFILE = "update_profile"
    ADD_DELEGATE = "add_delegate"
    REMOVE_DELEGATE = "remove_delegate"
    TRANSFER = "transfer"

    CHOICES = {LOGIN, UPDATE_PROFILE, ADD_DELEGATE, REMOVE_DELEGATE, TRANSFER}

# ============================================================
# Verification Endpoint Serializers
# ===========================================================
class VerificationChallengeSerializer(serializers.ModelSerializer):
    is_expired = serializers.BooleanField(read_only=True)
    class Meta:
        model = VerificationChallenge
        fields = [
            "id",
            "attempt_number",
            "expires_at",
            "is_expired",
        ]

# ============================================================
# Internal Serializers (for internal use, not exposed via API)
# ============================================================
class VerificationChallengeInternalSerializer(serializers.ModelSerializer):
    class Meta:
        model = VerificationChallenge
        fields = '__all__'


class CreateSessionSerializer(serializers.Serializer):
    organization_api_key = serializers.CharField(required=True,write_only=True,max_length=255,trim_whitespace=True)
    external_user_ref    = serializers.CharField(required=True,write_only=True,max_length=255,trim_whitespace=True)
    org_operation_ref    = serializers.CharField(required=True,write_only=True,max_length=255,trim_whitespace=True)
    operation_type       = serializers.CharField(required=True ,write_only=True,max_length=255,trim_whitespace=True)
    
    def validate_organization_api_key(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("API key is required")
        if len(value) < 20:
            raise serializers.ValidationError("Invalid API key format")
        return value

    def validate_org_operation_ref(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Operation reference cannot be empty")
        return value

    def validate_operation_type(self, value):
        value = value.strip().lower()
        if value not in OperationType.CHOICES:
            raise serializers.ValidationError("Invalid operation type")
        return value

    def validate(self, data):
        if data["operation_type"] == OperationType.TRANSFER:
            if not data["org_operation_ref"].startswith("txn_"):
                raise serializers.ValidationError({
                    "org_operation_ref": "Transfer operations must start with 'txn_'"
                })
        return data

class VerifySessionSerializer(serializers.Serializer):
    session_id = serializers.UUIDField()
    device_id = serializers.UUIDField()
    signature = serializers.CharField(max_length=4096, trim_whitespace=True)

    def validate_signature(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Signature is required")
        try:
            import base64
            base64.b64decode(value, validate=True)
        except Exception:
            raise serializers.ValidationError("Invalid signature format")
        return value
    def validate(self, data):
        session_id = data.get("session_id")
        if not VerificationSession.objects.filter(id=session_id).exists():
            raise serializers.ValidationError("Session not found")
        return data

class SessionStatusSerializer(serializers.ModelSerializer):
    is_expired = serializers.BooleanField(read_only=True)
    is_final = serializers.BooleanField(read_only=True)
    can_be_verified = serializers.BooleanField(read_only=True)
    attempts_exhausted = serializers.BooleanField(read_only=True)
    remaining_attempts = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = VerificationSession
        fields = [
            "id",
            "status",
            "operation_type",
            "org_operation_ref",
            "verified_at",
            "expires_at",
            "failure_reason",
            "attempt_count",
            "max_attempts",
            "is_expired",
            "is_final",
            "can_be_verified",
            "attempts_exhausted",
            "remaining_attempts",
            "created_at",
        ]
        read_only_fields = fields

# ============================================================
# Logs
# ============================================================
class AuditLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuditLog
        fields = [
            "id",
            "organization_id",
            "session_id",
            "device_id",
            "actor_type",
            "actor_id",
            "action",
            "result",
            "ip_address",
            "created_at",
            "metadata",
        ]
        read_only_fields = fields
        
class KeyUsageLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = KeyUsageLog
        fields = [
            "id",
            "organization_id",
            "device_id",
            "device_key_id",
            "session_id",
            "challenge_id",
            "action",
            "result",
            "failure_reason",
            "created_at",
            "metadata",
        ]
        read_only_fields = fields