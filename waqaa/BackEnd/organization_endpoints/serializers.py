from rest_framework import serializers

from accounts_endpoints.serializers import UserSerializer
from verification_endpoint.models import VerificationSession
from .models import Organization, OrganizationApiKey, OrganizationUser


class OrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = ['id', 'name', 'status', 'created_at']

class OrganizationApiKeySerializer(serializers.ModelSerializer):
    organization_detail = OrganizationSerializer(source='organization', read_only=True)

    class Meta:
        model = OrganizationApiKey
        fields = [
            'id',
            'organization',
            'organization_detail',
            'label',
            'scopes',
            'is_active',
            'last_used_at',
            'expires_at',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'last_used_at']

class OrganizationUserSerializer(serializers.ModelSerializer):
    user_detail = UserSerializer(source='user', read_only=True)
    organization_detail = OrganizationSerializer(source='organization', read_only=True)

    class Meta:
        model = OrganizationUser
        fields = [
            'id',
            'organization',
            'organization_detail',
            'user',
            'user_detail',
            'external_user_ref',
            'status',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at']

# للمنظمه تعرف حاله السيشن
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


class LinkUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrganizationUser
        fields = ['organization', 'user', 'external_user_ref']

    def validate(self, data):
        organization = data['organization']
        user = data['user']
        external_user_ref = data['external_user_ref']

        # ❌ منع التكرار (user + organization)
        if OrganizationUser.objects.filter(
            organization=organization,
            user=user
        ).exists():
            raise serializers.ValidationError({
                "detail": "User already linked to this organization"
            })

        # ❌ منع تكرار external_user_ref داخل نفس المنظمة
        if OrganizationUser.objects.filter(
            organization=organization,
            external_user_ref=external_user_ref
        ).exists():
            raise serializers.ValidationError({
                "detail": "external_user_ref already exists in this organization"
            })

        return data

    def create(self, validated_data):
        return OrganizationUser.objects.create(**validated_data)

