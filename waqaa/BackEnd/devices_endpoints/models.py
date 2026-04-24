import uuid
from django.db import models
from accounts_endpoints.models import WaqaUser
from organization_endpoints.models import Organization, OrganizationUser
# ============================================================
# Device
# ============================================================

class Device(models.Model):
    PLATFORM_CHOICES = [
        ('android', 'Android'), ('ios', 'iOS'),
        ('web', 'Web'), ('desktop', 'Desktop')
    ]

    id              = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user            = models.ForeignKey(WaqaUser, on_delete=models.CASCADE, related_name='devices')
    label           = models.TextField(null=True, blank=True)
    platform        = models.CharField(max_length=20, choices=PLATFORM_CHOICES)
    app_instance_id = models.CharField(max_length=100, null=True, blank=True)
    is_active       = models.BooleanField(default=True)
    is_primary_device = models.BooleanField(default=False)
    created_at      = models.DateTimeField(auto_now_add=True)
    updated_at      = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'devices'

    def __str__(self):
        return f"{self.user} — {self.platform} ({self.id})"
# ============================================================
# Device Key
# ============================================================
class DeviceKey(models.Model):
    PURPOSE_CHOICES  = [('auth', 'Auth'), ('approval', 'Approval')]
    ALGORITHM_CHOICES = [('ES256', 'ES256'), ('ES384', 'ES384'), ('RS256', 'RS256'), ('Ed25519', 'Ed25519')]
    FORMAT_CHOICES   = [('COSE', 'COSE'), ('JWK', 'JWK'), ('PEM', 'PEM'), ('RAW', 'RAW')]

    id                = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    device            = models.ForeignKey(Device, on_delete=models.CASCADE, related_name='keys')
    organization      = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='device_keys')
    key_purpose       = models.CharField(max_length=20, choices=PURPOSE_CHOICES)
    algorithm         = models.CharField(max_length=20, choices=ALGORITHM_CHOICES)
    key_format        = models.CharField(max_length=10, choices=FORMAT_CHOICES)
    public_key        = models.TextField()
    attestation_type  = models.CharField(max_length=50, null=True, blank=True)
    attestation_data  = models.JSONField(null=True, blank=True)
    is_active         = models.BooleanField(default=True)
    last_used_at      = models.DateTimeField(null=True, blank=True)
    revoked_at        = models.DateTimeField(null=True, blank=True)
    revocation_reason = models.CharField(max_length=255, null=True, blank=True)
    created_at        = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'device_keys'
        unique_together = [('device', 'organization', 'key_purpose')]

    def __str__(self):
        return f"{self.device} — {self.key_purpose} ({self.algorithm})"
    
   

# ============================================================
# Audit Logs (Append-only, no FK)
# ============================================================

class DeviceRevocationLog(models.Model):
    ACTOR_CHOICES = [('org', 'Org'), ('user', 'User'), ('system', 'System')]

    id                    = models.BigAutoField(primary_key=True)
    device_id             = models.UUIDField()
    user_id               = models.UUIDField(null=True, blank=True)
    revoked_by_actor_type = models.TextField(choices=ACTOR_CHOICES)
    revoked_by_actor_id   = models.UUIDField(null=True, blank=True)
    reason                = models.TextField(null=True, blank=True)
    created_at            = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'device_revocation_log'
        managed  = False  # no FK — immutable log


