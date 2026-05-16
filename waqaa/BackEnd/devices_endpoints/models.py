# FULL corrected file

import uuid

from django.db import models
from django.db.models import Q

from accounts_endpoints.models import AccountUser
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

    user = models.ForeignKey(
        AccountUser,
        on_delete=models.CASCADE,
        related_name="devices",
    )

    label = models.CharField(
        max_length=100,
        null=True,
        blank=True,
    )

    platform = models.CharField(
        max_length=20,
        choices=PLATFORM_CHOICES,
    )

    app_instance_id = models.CharField(
        max_length=100,
        null=True,
        blank=True,
    )

    is_active = models.BooleanField(default=True)

    # NEW
    # trusted devices allowed for verification flows

    is_trusted = models.BooleanField(default=False)

    is_primary_device = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:

        db_table = "devices"

        constraints = [
            models.UniqueConstraint(
                fields=["user", "app_instance_id"],
                name="unique_app_instance_per_user",
            ),

            models.UniqueConstraint(
                fields=["user"],
                condition=Q(is_primary_device=True),
                name="unique_primary_device_per_user",
            ),
        ]

    @property
    def active_key(self):

        return (
            self.keys.filter(is_active=True)
            .order_by("-created_at")
            .first()
        )

    def __str__(self):
        return f"{self.user} - {self.platform} ({self.id})"

# ============================================================
# Device Key
# ============================================================

class DeviceKey(models.Model):

    PURPOSE_CHOICES = [
        ("auth", "Auth"),
        ("approval", "Approval"),
    ]

    ALGORITHM_CHOICES = [
        ("ES256", "ES256"),
        ("ES384", "ES384"),
        ("RS256", "RS256"),
        ("Ed25519", "Ed25519"),
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

    key_purpose = models.CharField(
        max_length=20,
        choices=PURPOSE_CHOICES,
    )

    algorithm = models.CharField(
        max_length=20,
        choices=ALGORITHM_CHOICES,
    )

    key_format = models.CharField(
        max_length=10,
        choices=FORMAT_CHOICES,
    )

    public_key = models.TextField()

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
            models.UniqueConstraint(
                fields=["device", "organization", "key_purpose"],
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
            f"{self.key_purpose} "
            f"({self.algorithm})"
        )


# ============================================================
# Device Revocation Log
# ============================================================

class DeviceRevocationLog(models.Model):

    ACTOR_CHOICES = [
        ("org", "Organization"),
        ("user", "User"),
        ("system", "System"),
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
        db_table = "device_revocation_log"

    def __str__(self):
        return (
            f"RevocationLog[{self.id}] "
            f"{self.revoked_by_actor_type} - "
            f"{self.reason or 'no_reason'}"
        )
    
