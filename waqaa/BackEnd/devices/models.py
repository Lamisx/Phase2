#from django.db import models
#class Device(models.Model):
    #device_id = models.CharField(max_length=255, unique=True)
   
#status = models.CharField(max_length=20, default="PENDING")

    #def __str__(self):
      #  return self.device_id





import uuid
from django.db import models
from django.contrib.postgres.fields import ArrayField


# ============================================================
# Organization
# ============================================================

class Organization(models.Model):
    STATUS_CHOICES = [('active', 'Active'), ('suspended', 'Suspended')]

    id         = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name       = models.TextField(unique=True)
    status     = models.TextField(default='active', choices=STATUS_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'organizations'

    def __str__(self):
        return self.name


class OrganizationApiKey(models.Model):
    SCOPE_CHOICES = [
        'session:create', 'session:read', 'session:cancel',
        'audit:read', 'device:revoke'
    ]

    id              = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization    = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='api_keys')
    key_hash        = models.TextField(unique=True)
    label           = models.TextField(null=True, blank=True)
    scopes          = ArrayField(models.TextField(), default=list)
    is_active       = models.BooleanField(default=True)
    last_used_at    = models.DateTimeField(null=True, blank=True)
    expires_at      = models.DateTimeField(null=True, blank=True)
    created_at      = models.DateTimeField(auto_now_add=True)
    updated_at      = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'organization_api_keys'

    def __str__(self):
        return f"{self.organization.name} — {self.label or self.id}"


# ============================================================
# User
# ============================================================

class WaqaUser(models.Model):
    STATUS_CHOICES = [('active', 'Active'), ('suspended', 'Suspended'), ('deleted', 'Deleted')]

    id               = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    username         = models.TextField(null=True, blank=True, unique=True)
    display_name     = models.TextField(null=True, blank=True)
    email            = models.TextField(null=True, blank=True)
    phone            = models.TextField(null=True, blank=True)
    national_id_hmac = models.TextField(null=True, blank=True)
    status           = models.TextField(default='active', choices=STATUS_CHOICES)
    created_at       = models.DateTimeField(auto_now_add=True)
    updated_at       = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'users'

    def __str__(self):
        return self.username or self.display_name or str(self.id)


class OrganizationUser(models.Model):
    STATUS_CHOICES = [
        ('linked', 'Linked'), ('pending', 'Pending'),
        ('suspended', 'Suspended'), ('unlinked', 'Unlinked')
    ]

    id                = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization      = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='org_users')
    user              = models.ForeignKey(WaqaUser, on_delete=models.CASCADE, related_name='org_links')
    external_user_ref = models.TextField()
    status            = models.TextField(default='linked', choices=STATUS_CHOICES)
    created_at        = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'organization_users'
        unique_together = [
            ('organization', 'external_user_ref'),
            ('organization', 'user'),
        ]

    def __str__(self):
        return f"{self.organization.name} — {self.external_user_ref}"


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
    platform        = models.TextField(choices=PLATFORM_CHOICES)
    app_instance_id = models.TextField(null=True, blank=True)
    is_active       = models.BooleanField(default=True)
    created_at      = models.DateTimeField(auto_now_add=True)
    updated_at      = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'devices'

    def __str__(self):
        return f"{self.user} — {self.platform} ({self.id})"


class DeviceKey(models.Model):
    PURPOSE_CHOICES  = [('auth', 'Auth'), ('approval', 'Approval')]
    ALGORITHM_CHOICES = [('ES256', 'ES256'), ('ES384', 'ES384'), ('RS256', 'RS256'), ('Ed25519', 'Ed25519')]
    FORMAT_CHOICES   = [('COSE', 'COSE'), ('JWK', 'JWK'), ('PEM', 'PEM'), ('RAW', 'RAW')]

    id                = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    device            = models.ForeignKey(Device, on_delete=models.CASCADE, related_name='keys')
    organization      = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='device_keys')
    key_purpose       = models.TextField(choices=PURPOSE_CHOICES)
    algorithm         = models.TextField(choices=ALGORITHM_CHOICES)
    key_format        = models.TextField(choices=FORMAT_CHOICES)
    public_key        = models.TextField()
    attestation_type  = models.TextField(null=True, blank=True)
    attestation_data  = models.JSONField(null=True, blank=True)
    is_active         = models.BooleanField(default=True)
    last_used_at      = models.DateTimeField(null=True, blank=True)
    revoked_at        = models.DateTimeField(null=True, blank=True)
    revocation_reason = models.TextField(null=True, blank=True)
    created_at        = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'device_keys'

    def __str__(self):
        return f"{self.device} — {self.key_purpose} ({self.algorithm})"


# ============================================================
# Verification Session
# ============================================================

class VerificationSession(models.Model):
    STATUS_CHOICES = [
        ('pending',          'Pending'),
        ('challenge_issued', 'Challenge Issued'),
        ('awaiting_user',    'Awaiting User'),
        ('verified',         'Verified'),
        ('denied',           'Denied'),
        ('failed',           'Failed'),
        ('expired',          'Expired'),
        ('cancelled',        'Cancelled'),
    ]

    id                          = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization                = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='sessions')
    org_user                    = models.ForeignKey(OrganizationUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='sessions')
    device                      = models.ForeignKey(Device, on_delete=models.SET_NULL, null=True, blank=True, related_name='sessions')
    org_operation_ref           = models.TextField()
    operation_type              = models.TextField()
    operation_hash              = models.TextField(null=True, blank=True)
    operation_payload_encrypted = models.TextField(null=True, blank=True)
    status                      = models.TextField(default='pending', choices=STATUS_CHOICES)
    nonce                       = models.TextField(unique=True)
    attempt_count               = models.IntegerField(default=0)
    max_attempts                = models.IntegerField(default=3)
    decision_token_hash         = models.TextField(null=True, blank=True)
    client_ip                   = models.GenericIPAddressField(null=True, blank=True)
    user_agent                  = models.TextField(null=True, blank=True)
    verified_at                 = models.DateTimeField(null=True, blank=True)
    failure_reason              = models.TextField(null=True, blank=True)
    created_at                  = models.DateTimeField(auto_now_add=True)
    expires_at                  = models.DateTimeField()

    class Meta:
        db_table = 'verification_sessions'
        unique_together = [('organization', 'org_operation_ref')]

    def __str__(self):
        return f"{self.organization} — {self.operation_type} ({self.status})"


# ============================================================
# Verification Challenge
# ============================================================

class VerificationChallenge(models.Model):
    id              = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session         = models.ForeignKey(VerificationSession, on_delete=models.CASCADE, related_name='challenges')
    challenge_bytes = models.TextField()
    attempt_number  = models.IntegerField()
    is_active       = models.BooleanField(default=True)
    is_used         = models.BooleanField(default=False)
    used_at         = models.DateTimeField(null=True, blank=True)
    expires_at      = models.DateTimeField()
    created_at      = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'verification_challenges'
        unique_together = [('session', 'attempt_number')]

    def __str__(self):
        return f"Challenge {self.attempt_number} — session {self.session_id}"


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


class AuditLog(models.Model):
    ACTOR_CHOICES  = [('org', 'Org'), ('user', 'User'), ('system', 'System')]
    RESULT_CHOICES = [('ok', 'OK'), ('fail', 'Fail')]

    id              = models.BigAutoField(primary_key=True)
    organization_id = models.UUIDField(null=True, blank=True)
    session_id      = models.UUIDField(null=True, blank=True)
    device_id       = models.UUIDField(null=True, blank=True)
    actor_type      = models.TextField(choices=ACTOR_CHOICES)
    actor_id        = models.UUIDField(null=True, blank=True)
    action          = models.TextField()
    result          = models.TextField(choices=RESULT_CHOICES)
    ip_address      = models.GenericIPAddressField(null=True, blank=True)
    created_at      = models.DateTimeField(auto_now_add=True)
    metadata        = models.JSONField(null=True, blank=True)

    class Meta:
        db_table = 'audit_log'
        managed  = False  # no FK — immutable log


class KeyUsageLog(models.Model):
    ACTION_CHOICES = [('sign', 'Sign'), ('verify', 'Verify')]
    RESULT_CHOICES = [('ok', 'OK'), ('fail', 'Fail')]

    id              = models.BigAutoField(primary_key=True)
    organization_id = models.UUIDField(null=True, blank=True)
    device_id       = models.UUIDField(null=True, blank=True)
    device_key_id   = models.UUIDField(null=True, blank=True)
    session_id      = models.UUIDField(null=True, blank=True)
    challenge_id    = models.UUIDField(null=True, blank=True)
    action          = models.TextField(choices=ACTION_CHOICES)
    result          = models.TextField(choices=RESULT_CHOICES)
    failure_reason  = models.TextField(null=True, blank=True)
    created_at      = models.DateTimeField(auto_now_add=True)
    metadata        = models.JSONField(null=True, blank=True)

    class Meta:
        db_table = 'key_usage_log'
        managed  = False  # no FK — immutable log


# ============================================================
# Delegated Access
# ============================================================

class DelegatedAccess(models.Model):
    ADDED_VIA_CHOICES = [('qr', 'QR'), ('otp', 'OTP')]
    STATUS_CHOICES    = [('active', 'Active'), ('revoked', 'Revoked')]

    id                   = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    primary_org_user     = models.ForeignKey(OrganizationUser, on_delete=models.CASCADE, related_name='delegated_to')
    delegate_org_user    = models.ForeignKey(OrganizationUser, on_delete=models.CASCADE, related_name='delegated_from')
    added_via            = models.TextField(choices=ADDED_VIA_CHOICES)
    status               = models.TextField(default='active', choices=STATUS_CHOICES)
    created_at           = models.DateTimeField(auto_now_add=True)
    revoked_at           = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'delegated_access'
        unique_together = [('primary_org_user', 'delegate_org_user')]

    def __str__(self):
        return f"{self.primary_org_user} → {self.delegate_org_user}"
