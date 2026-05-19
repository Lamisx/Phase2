# devices_endpoints/models.py (Final Recommended Version)

import uuid

from django.conf import settings
from django.db import models
from django.db.models import Q

from organization_endpoints.models import Organization


# ============================================================
# Device
# ============================================================
class Device(models.Model):

    PLATFORM_CHOICES = [
        ("android", "Android"),
        ("ios", "iOS"),
        ("web", "Web"),
        ("desktop", "Desktop"),
    ]

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    # Device owner
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="devices",
    )

    # Friendly device name shown to user
    label = models.CharField(
        max_length=100,
        null=True,
        blank=True,
    )

    # android / ios / web
    platform = models.CharField(
        max_length=20,
        choices=PLATFORM_CHOICES,
    )

    # Unique app installation identifier
    app_instance_id = models.CharField(
        max_length=100,
        null=True,
        blank=True,
    )

    # Device still allowed to operate?
    is_active = models.BooleanField(default=True)

    # Trusted by Waqaa?
    is_trusted = models.BooleanField(default=False)

    # Main user device?
    is_primary_device = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "devices"

        constraints = [

            # User can only have one primary device
            models.UniqueConstraint(
                fields=["user"],
                condition=Q(is_primary_device=True),
                name="unique_primary_device_per_user",
            ),

            # Prevent duplicate app installations
            models.UniqueConstraint(
                fields=["user", "app_instance_id"],
                name="unique_app_instance_per_user",
            ),
        ]

        indexes = [
            models.Index(fields=["user", "is_active"]),
            models.Index(fields=["app_instance_id"]),
        ]

    def __str__(self):
        return f"{self.user} - {self.platform} ({self.id})"

    # ========================================================
    # Helpers
    # ========================================================

    @property
    def active_key(self):
        """
        Returns latest active key.

        Useful when device only has one active scope.
        """

        return (
            self.keys
            .filter(is_active=True)
            .order_by("-created_at")
            .first()
        )

    def get_active_key(
        self,
        *,
        organization,
        key_purpose="auth",
    ):
        """
        Returns organization-scoped active key.
        """

        return self.keys.filter(
            organization=organization,
            key_purpose=key_purpose,
            is_active=True,
        ).first()


# ============================================================
# Device Key
# ============================================================
class DeviceKey(models.Model):

    PURPOSE_AUTH = "auth"
    PURPOSE_APPROVAL = "approval"

    PURPOSE_CHOICES = [
        (PURPOSE_AUTH, "Auth"),
        (PURPOSE_APPROVAL, "Approval"),
    ]

    # Final algorithms
    # ES256 = recommended default
    ALGORITHM_CHOICES = [
        ("ES256", "ES256"),
        ("ES384", "ES384"),
        ("RS256", "RS256"),
    ]

    FORMAT_CHOICES = [
        ("COSE", "COSE"),
        ("JWK", "JWK"),
        ("PEM", "PEM"),
        ("RAW", "RAW"),
    ]

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    device = models.ForeignKey(
        Device,
        on_delete=models.CASCADE,
        related_name="keys",
    )

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="device_keys",
    )

    # auth / approval
    key_purpose = models.CharField(
        max_length=20,
        choices=PURPOSE_CHOICES,
    )

    # ES256
    algorithm = models.CharField(
        max_length=20,
        choices=ALGORITHM_CHOICES,
    )

    # RAW / PEM / JWK
    key_format = models.CharField(
        max_length=10,
        choices=FORMAT_CHOICES,
    )

    # Public key only
    # Private key NEVER reaches backend
    public_key = models.TextField()

    # Future hardware attestation
    attestation_type = models.CharField(
        max_length=50,
        null=True,
        blank=True,
    )

    attestation_data = models.JSONField(
        null=True,
        blank=True,
    )

    is_active = models.BooleanField(default=True)

    last_used_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    revoked_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    revocation_reason = models.CharField(
        max_length=255,
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "device_keys"

        constraints = [

            # One active key per:
            # device + organization + purpose
            models.UniqueConstraint(
                fields=[
                    "device",
                    "organization",
                    "key_purpose",
                ],
                condition=Q(is_active=True),
                name="unique_active_device_key_per_scope",
            ),
        ]

        indexes = [
            models.Index(fields=["device", "is_active"]),
            models.Index(fields=["organization", "is_active"]),
        ]

    def __str__(self):
        return (
            f"{self.device} - "
            f"{self.key_purpose} ({self.algorithm})"
        )


# ============================================================
# Device Revocation Log
# ============================================================
class DeviceRevocationLog(models.Model):
    """
    Immutable audit trail for revoked devices.

    Uses raw UUID fields so logs survive deletion.
    """

    ACTOR_ORG = "org"
    ACTOR_USER = "user"
    ACTOR_SYSTEM = "system"

    ACTOR_CHOICES = [
        (ACTOR_ORG, "Organization"),
        (ACTOR_USER, "User"),
        (ACTOR_SYSTEM, "System"),
    ]

    id = models.BigAutoField(primary_key=True)

    device_id = models.UUIDField()

    user_id = models.UUIDField(
        null=True,
        blank=True,
    )

    revoked_by_actor_type = models.CharField(
        max_length=10,
        choices=ACTOR_CHOICES,
    )

    revoked_by_actor_id = models.UUIDField(
        null=True,
        blank=True,
    )

    reason = models.TextField(
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "device_revocation_logs"

        indexes = [
            models.Index(fields=["device_id"]),
            models.Index(fields=["user_id"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return f"RevocationLog({self.device_id})"


# After Saving
