"""Organization serializers."""
from rest_framework import serializers

from .models import Organization, OrganizationApiKey, OrganizationUser


class OrganizationSerializer(serializers.ModelSerializer):
    """Read-only organization summary. Never exposes sensitive fields."""

    class Meta:
        model = Organization
        fields = ["id", "name", "status", "created_at", "updated_at"]
        read_only_fields = fields


class OrganizationApiKeySerializer(serializers.ModelSerializer):
    """Read-only API key view. Never exposes key_hash or plaintext."""

    organization_detail = OrganizationSerializer(source="organization", read_only=True)

    class Meta:
        model = OrganizationApiKey
        fields = [
            "id",
            "organization",
            "organization_detail",
            "label",
            "scopes",
            "is_active",
            "rate_limit_per_minute",
            "revoked_at",
            "last_used_at",
            "expires_at",
            "created_at",
            "updated_at",
        ]
        # Read-only — write paths go through services.
        read_only_fields = fields


class OrganizationUserSerializer(serializers.ModelSerializer):
    """Read-only link summary."""

    organization_detail = OrganizationSerializer(source="organization", read_only=True)
    user_username = serializers.CharField(source="user.username", read_only=True)
    user_display_name = serializers.CharField(source="user.display_name", read_only=True)

    class Meta:
        model = OrganizationUser
        fields = [
            "id",
            "organization",
            "organization_detail",
            "user",
            "user_username",
            "user_display_name",
            "external_provider",
            "external_user_ref",
            "role",
            "status",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class LinkUserSerializer(serializers.Serializer):
    """Input for linking a Waqa AccountUser to the calling organization.

    The organization identifies the user by the SHA-256 hash of their
    national ID — the organization already has the national ID for its
    own customer onboarding, so it can compute this hash without
    knowing any Waqa secret.

    The organization is taken from request.organization (the authenticated
    API key), NEVER from request data — otherwise any key would be able
    to create links in any organization.
    """
 
    external_user_ref = serializers.CharField(max_length=255,trim_whitespace=True,)

    national_id_hash = serializers.CharField(
        max_length=128,
        min_length=64,
        help_text="SHA-256 hex of the user's national ID (64 hex chars).",
    )
    external_user_ref = serializers.CharField(
        max_length=255,
        help_text="The organization's identifier for this user (e.g. customer ID).",
    )
    external_provider = serializers.ChoiceField(
        choices=[c[0] for c in OrganizationUser.PROVIDER_CHOICES],
        default=OrganizationUser.PROVIDER_INTERNAL,
    )
    role = serializers.ChoiceField(
        choices=[c[0] for c in OrganizationUser.ROLE_CHOICES],
        default=OrganizationUser.ROLE_MEMBER,
    )

    def validate_external_user_ref(self, value):

        value = value.strip()

        if not value:
            raise serializers.ValidationError(
                "External user ref is required."
            )

    def validate_national_id_hash(self, value):
        value = (value or "").strip().lower()
        # SHA-256 hex is exactly 64 lowercase hex chars.
        if len(value) != 64:
            raise serializers.ValidationError(
                "national_id_hash must be SHA-256 hex (64 characters)."
            )
        try:
            int(value, 16)
        except ValueError:
            raise serializers.ValidationError("national_id_hash must be a valid hex string.")
        return value

    def validate_external_user_ref(self, value):
        value = (value or "").strip()
        if not value:
            raise serializers.ValidationError("external_user_ref is required.")
        return value


























