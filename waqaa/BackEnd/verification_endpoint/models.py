from django.db import models
import uuid
from accounts_endpoints.models import WaqaUser
from organization_endpoints.models import Organization, OrganizationUser
from devices.models import Device
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
    verified_by_user            = models.ForeignKey(WaqaUser, on_delete=models.SET_NULL, null=True,blank=True, related_name="verified_sessions",)##هل التحقق تم بواسطة الـ primary？
    verified_by_actor_type      = models.TextField(choices=[("primary", "Primary"), ("delegate", "Delegate")],null=True,blank=True)# for audit
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
# AuditLog
# ============================================================
    

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


# ============================================================
# KeyUsageLog
# ============================================================

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



