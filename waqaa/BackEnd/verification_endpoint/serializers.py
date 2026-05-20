"""Verification endpoint serializers."""
import base64

from rest_framework import serializers

from .models import (
    AuditLog,
    KeyUsageLog,
    VerificationChallenge,
    VerificationSession,
)


# ============================================================
# Inputs
# ============================================================
class CreateSessionInputSerializer(serializers.Serializer):
    """Input for POST /api/verification/sessions/create/.

    The calling organization is identified by the X-API-Key header
    (OrganizationAPIKeyAuthentication), NEVER from this body.
    """

    external_user_ref = serializers.CharField(
        required=True, max_length=255, trim_whitespace=True,
    )
    org_operation_ref = serializers.CharField(
        required=True, max_length=255, trim_whitespace=True,
    )
    operation_type = serializers.ChoiceField(
        choices=VerificationSession.OperationType.choices,
        required=True,
    )
    operation_hash = serializers.CharField(
        required=False, allow_blank=True, max_length=128,
    )
    operation_payload_encrypted = serializers.CharField(
        required=False, allow_blank=True,
    )

    def validate_org_operation_ref(self, value):
        value = (value or "").strip()
        if not value:
            raise serializers.ValidationError("Operation reference cannot be empty.")
        return value

    def validate(self, data):
        # Business rule: TRANSFER operations must be referenced as "txn_*".
        if data.get("operation_type") == VerificationSession.OperationType.TRANSFER:
            ref = data.get("org_operation_ref", "")
            if not ref.startswith("txn_"):
                raise serializers.ValidationError({
                    "org_operation_ref": "Transfer operations must start with 'txn_'.",
                })
        return data


class VerifySignatureInputSerializer(serializers.Serializer):
    """Input for POST /api/verification/sessions/<id>/verify/ (no auth header).

    The device proves itself by signing the challenge with the private key
    whose public counterpart is registered on the server.
    """

    device_id = serializers.UUIDField()
    signature = serializers.CharField(max_length=4096, trim_whitespace=True)

    def validate_signature(self, value):
        value = (value or "").strip()
        if not value:
            raise serializers.ValidationError("Signature is required.")
        try:
            decoded = base64.b64decode(
                value,
                validate=True,
            )

            if len(decoded) < 64:
                raise serializers.ValidationError(
                    "Signature too short."
                )
        except Exception:
            raise serializers.ValidationError("Invalid signature format.")
        return value


# ============================================================
# Outputs
# ============================================================
class VerificationChallengeSerializer(serializers.ModelSerializer):
    """Public challenge representation (forensic listing)."""

    is_expired = serializers.BooleanField(read_only=True)

    class Meta:
        model = VerificationChallenge
        fields = [
            "id",
            "attempt_number",
            "expires_at",
            "is_expired",
            "is_active",
            "is_used",
            "used_at",
            "created_at",
        ]
        read_only_fields = fields


class SessionStatusSerializer(serializers.ModelSerializer):
    """Full session status payload — used in responses and polling."""

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
# Logs (read-only)
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
            "user_agent",
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