from time import timezone

from django.db import models
import uuid

from accounts_endpoints.models import WaqaUser
from organization_endpoints.models import Organization, OrganizationUser
from devices_endpoints.models import Device
<<<<<<< HEAD
from django.utils.translation import gettext_lazy as _ #لترجمة الحقول في لوحة الإدارة
# ===========================================================
=======


 # ============================================================
>>>>>>> 8c6f7098cf3d27df711aef655ba6e272d182b799
# Verification Session
# ============================================================

class VerificationSession(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending', _('Pending')
        CHALLENGE_ISSUED = 'challenge_issued', _('Challenge Issued')
        AWAITING_USER = 'awaiting_user', _('Awaiting User')
        VERIFIED = 'verified', _('Verified')
        DENIED = 'denied', _('Denied')
        FAILED = 'failed', _('Failed')
        EXPIRED = 'expired', _('Expired')
        CANCELLED = 'cancelled', _('Cancelled')

    class ActorType(models.TextChoices):
        PRIMARY = 'primary', _('Primary')
        DELEGATE = 'delegate', _('Delegate')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization                = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='sessions')
    org_user                    = models.ForeignKey(OrganizationUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='sessions')
    device                      = models.ForeignKey(Device, on_delete=models.SET_NULL, null=True, blank=True, related_name='sessions')
    verified_by_user            = models.ForeignKey(WaqaUser, on_delete=models.SET_NULL, null=True,blank=True, related_name="verified_sessions",)##هل التحقق تم بواسطة الـ primary？
    verified_by_actor_type      = models.CharField(max_length=15, choices=ActorType.choices, null=True, blank=True)# for audit
    org_operation_ref           = models.CharField(max_length=255)
    operation_type              = models.CharField(max_length=100)
    operation_hash              = models.CharField(max_length=128,null=True, blank=True)
    operation_payload_encrypted = models.TextField(null=True, blank=True)
    status                      = models.CharField(max_length=20,default=Status.PENDING, choices=Status.choices)
    nonce                       = models.CharField(max_length=64, unique=True)
    attempt_count               = models.IntegerField(default=0)
    max_attempts                = models.IntegerField(default=3)
    decision_token_hash         = models.CharField(max_length=128, null=True, blank=True)
    client_ip                   = models.GenericIPAddressField(null=True, blank=True)
    user_agent                  = models.TextField( null=True, blank=True)
    verified_at                 = models.DateTimeField(null=True, blank=True)
    failure_reason              = models.CharField(max_length=255, null=True, blank=True)
    created_at                  = models.DateTimeField(auto_now_add=True)
    expires_at                  = models.DateTimeField()
    

class Meta:
    db_table = 'verification_sessions'
    ordering = ['-created_at']

    constraints = [
        models.UniqueConstraint(
            fields=['organization', 'org_operation_ref'],
            name='uq_verification_session_org_operation_ref'
        )
    ]

    indexes = [
        models.Index(fields=['status', 'expires_at'], name='idx_vs_status_expires'),  
        models.Index(fields=['organization', 'created_at'], name='idx_vs_org_created'),
        models.Index(fields=['organization', 'status'],  name='idx_vs_org_status'),
        models.Index(fields=['org_user', 'status'], name='idx_vs_orguser_status'),
        models.Index(fields=['nonce']),
    ]

    def __str__(self):
        return f"{self.organization_id} | {self.operation_type} | {self.status}"

    @property
    def is_expired(self) -> bool:
        return timezone.now() >= self.expires_at

    @property
    def can_be_verified(self) -> bool:
        """هل الجلسة في حالة تسمح بالتحقق؟"""
        if self.is_expired:
            return False
        return self.status in [self.Status.CHALLENGE_ISSUED,
                               self.Status.PENDING, 
                               self.Status.AWAITING_USER]
    
    def mark_as_expired(self):
        if self.is_expired and self.status not in ['verified', 'failed', 'expired']:
            self.status = self.Status.EXPIRED
            self.failure_reason = 'session_expired'
            self.save(update_fields=['status', 'failure_reason'])
    def mark_expired_if_needed(self, commit=True):
        if not self.is_expired:
            return False
        if self.is_final:
            return False
        self.status = self.Status.EXPIRED
        self.failure_reason = "session_expired"
        if commit:
            self.save(update_fields=["status", "failure_reason"])
        return True
    def update_expired_status(self, commit: bool = True) -> bool:

        if not self.is_expired or self.is_final:
            return False
        self.status = self.Status.EXPIRED
        self.failure_reason = 'session_expired'
        if commit:
            self.save(update_fields=['status', 'failure_reason'])
        return True
    def mark_expired(self, commit: bool = True) -> bool:
       
        if self.is_final or not self.is_expired():
            return False
        self.status         = self.Status.EXPIRED
        self.failure_reason = 'session_expired'
        if commit:
            self.save(update_fields=['status', 'failure_reason'])
        return True
    def update_expired_status(self, commit=True):
     if not self.is_expired or self.is_final:
        return False
     self.status = self.Status.EXPIRED
     self.failure_reason = 'session_expired'
     if commit:
        self.save(update_fields=['status', 'failure_reason'])
     return True
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



