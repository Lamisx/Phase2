from rest_framework import serializers
from .models import AuditLog, KeyUsageLog, VerificationSession, VerificationChallenge

# ============================================================
# Session & Challenge
# ============================================================

class VerificationChallengeSerializer(serializers.ModelSerializer):
    class Meta:
        model = VerificationChallenge
        fields = [
            'id',
            'session',
            'challenge_bytes',
            'attempt_number',
            'is_active',
            'is_used',
            'used_at',
            'expires_at',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at']


class CreateSessionSerializer(serializers.Serializer):
    organization_api_key = serializers.CharField(required=True)
    external_user_ref    = serializers.CharField(required=True)
    org_operation_ref    = serializers.CharField(required=True)
    operation_type       = serializers.CharField(required=True)


class VerifySessionSerializer(serializers.Serializer):
    device_id = serializers.UUIDField()
    signature = serializers.CharField()


class SessionStatusSerializer(serializers.ModelSerializer):
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
        ]

# ============================================================
# Logs
# ============================================================

class AuditLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuditLog
        fields = '__all__'


class KeyUsageLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = KeyUsageLog
        fields = '__all__'