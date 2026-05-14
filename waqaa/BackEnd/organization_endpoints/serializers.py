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
        # Entire serializer is read-only — write paths go through services
        # (so secret generation, hashing, and audit logging stay centralized).
        read_only_fields = fields
 
 
class OrganizationUserSerializer(serializers.ModelSerializer):
    """Read-only link summary."""
 
    organization_detail = OrganizationSerializer(source="organization", read_only=True)
    user_username = serializers.CharField(source="user.username", read_only=True)
 
    class Meta:
        model = OrganizationUser
        fields = [
            "id",
            "organization",
            "organization_detail",
            "user",
            "user_username",
            "external_provider",
            "external_user_ref",
            "role",
            "status",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields
 
 
class LinkUserSerializer(serializers.Serializer):
    """
    Input for linking an AccountUser to the calling organization.
 
    `organization` is taken from request.organization (the authenticated
    API key), NEVER from request data — otherwise any key would be able
    to create links in any organization.
    """
 
    user_id = serializers.UUIDField()
    external_user_ref = serializers.CharField(max_length=255)
    external_provider = serializers.ChoiceField(
        choices=[c[0] for c in OrganizationUser.PROVIDER_CHOICES],
        default=OrganizationUser.PROVIDER_INTERNAL,
    )
    role = serializers.ChoiceField(
        choices=[c[0] for c in OrganizationUser.ROLE_CHOICES],
        default=OrganizationUser.ROLE_MEMBER,
    )