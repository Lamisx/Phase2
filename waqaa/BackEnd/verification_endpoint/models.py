from django.utils import timezone
from django.db import models
import uuid
from accounts_endpoints.models import WaqaUser
from organization_endpoints.models import Organization, OrganizationUser
from devices_endpoints.models import Device

from django.utils.translation import gettext_lazy as _ #لترجمة الحقول في لوحة الإدارة

# ============================================================
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
    organization                = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='verification_sessions')
    org_user                    = models.ForeignKey(OrganizationUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='verification_sessions')
    device                      = models.ForeignKey(Device, on_delete=models.SET_NULL, null=True, blank=True, related_name='verification_sessions')
    verified_by_user            = models.ForeignKey(WaqaUser, on_delete=models.SET_NULL, null=True,blank=True, related_name="verified_sessions",)##هل التحقق تم بواسطة الـ primary？
    verified_by_actor_type      = models.CharField(max_length=10, choices=ActorType.choices, null=True, blank=True)# for audit
    org_operation_ref           = models.CharField(max_length=255)
    operation_type              = models.CharField(max_length=100)
    operation_hash              = models.CharField(max_length=128,null=True, blank=True)
    operation_payload_encrypted = models.TextField(null=True, blank=True)
    status                      = models.CharField(max_length=20,default=Status.PENDING, choices=Status.choices)
    nonce                       = models.CharField(max_length=64, unique=True)
    attempt_count               = models.PositiveIntegerField(default=0)
    max_attempts                = models.PositiveIntegerField(default=3)
    decision_token_hash         = models.CharField(max_length=128, null=True, blank=True)
    client_ip                   = models.GenericIPAddressField(null=True, blank=True)
    user_agent                  = models.CharField(max_length=512, null=True, blank=True)
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
            models.Index(fields=['organization', 'status'],  name='idx_vs_org_status'),
            models.Index(fields=['org_user', 'status'], name='idx_vs_orguser_status'),
            #models.Index(fields=['nonce'], name='idx_vs_nonce'),
        ]

    def __str__(self):
        return f"{self.organization_id} | {self.operation_type} | {self.status}"
# ---------- State helpers ----------
    @property
    def is_expired(self) -> bool:
        return timezone.now() >= self.expires_at
    @property
    def is_final(self) -> bool:
        """جلسة في حالة نهائية لا يمكن تعديلها."""
        return self.status in {
            self.Status.VERIFIED,
            self.Status.DENIED,
            self.Status.FAILED,
            self.Status.EXPIRED,
            self.Status.CANCELLED,
        }
    @property
    def can_be_verified(self) -> bool:
        """هل يمكن تنفيذ التحقق على هذه الجلسة حالياً؟"""
        if self.is_expired or self.is_final:
            return False
        return self.status in {
            self.Status.CHALLENGE_ISSUED,
            self.Status.AWAITING_USER,
        }
# ---------- Attempts ----------
    @property
    def attempts_exhausted(self) -> bool:
        """هل استُنفدت جميع محاولات التحقق؟"""
        return self.attempt_count >= self.max_attempts
    @property
    def remaining_attempts(self) -> int:
        """عدد المحاولات المتبقية."""
        return max(0, self.max_attempts - self.attempt_count)
#---------- Status updates ----------
    def update_expired_status(self, commit: bool = True) -> bool:
        """
        يحدّث الجلسة إلى EXPIRED إذا انتهت صلاحيتها ولم تكن نهائية.
        يعيد True إذا تم التحديث، و False إذا لم يتغير شيء.
        """
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
    attempt_number  = models.PositiveSmallIntegerField()
    is_active       = models.BooleanField(default=True)
    is_used         = models.BooleanField(default=False)
    used_at         = models.DateTimeField(null=True, blank=True)
    expires_at      = models.DateTimeField()
    created_at      = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'verification_challenges'
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['session', 'attempt_number'],
                name='uq_challenge_session_attempt'
            )
        ]
        indexes = [
            models.Index(fields=['session', 'is_active', 'is_used'], name='idx_challenge_active_used'),
            models.Index(fields=['expires_at'], name='idx_challenge_expires'),
        ]
        

    def __str__(self):
        return f"Challenge {self.attempt_number} — session {self.session_id}"
    

    @property
    def is_expired(self) -> bool:
        return timezone.now() >= self.expires_at
    
    @property
    def is_valid(self) -> bool:
        """التحدي صالح للاستخدام — نشط، غير مستخدم، وغير منتهي."""
        return (
            self.is_active
            and not self.is_used
            and not self.is_expired
        )
    '''  هل احتاج هذا ؟ او لا ؟ 
    def mark_as_used(self, commit: bool = True) -> bool:
        """يعلّم التحدي كمستخدم ويوقفه."""
        if self.is_used or not self.is_active:
            return False
        self.is_used = True
        self.is_active = False
        self.used_at = timezone.now()
        if commit:
            self.save(update_fields=['is_used', 'is_active', 'used_at'])
        return True
    '''
# ============================================================
# AuditLog
# ============================================================
    

class AuditLog(models.Model):
    class ActorType(models.TextChoices):
        ORG = 'org', _('Org')
        USER = 'user', _('User')
        SYSTEM = 'system', _('System')

    class Result(models.TextChoices):
        OK = 'ok', _('OK')
        FAIL = 'fail', _('Fail')

    id              = models.BigAutoField(primary_key=True)
    organization_id = models.UUIDField(null=True, blank=True)
    session_id      = models.UUIDField(null=True, blank=True)
    device_id       = models.UUIDField(null=True, blank=True)
    actor_type      = models.CharField(max_length=10, choices=ActorType.choices)
    actor_id        = models.UUIDField(null=True, blank=True)
    action          = models.CharField(max_length=100)
    result          = models.CharField(max_length=10, choices=Result.choices)
    ip_address      = models.GenericIPAddressField(null=True, blank=True)
    created_at      = models.DateTimeField(auto_now_add=True)
    metadata        = models.JSONField(null=True, blank=True)

    class Meta:
        db_table = 'audit_log'
        managed  = False  # no FK — immutable log
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['organization_id', 'created_at'], name='idx_audit_org_created'),
            models.Index(fields=['session_id', 'created_at'], name='idx_audit_session_created'),
        ]
    def __str__(self):
        return f"Audit {self.id} — {self.actor_type} {self.action} ({self.result})"

# ============================================================
# KeyUsageLog
# ============================================================

class KeyUsageLog(models.Model):
    class Action(models.TextChoices):
        SIGN = 'sign', _('Sign')
        VERIFY = 'verify', _('Verify')

    class Result(models.TextChoices):
        OK = 'ok', _('OK')
        FAIL = 'fail', _('Fail')
    id              = models.BigAutoField(primary_key=True)
    organization_id = models.UUIDField(null=True, blank=True)
    device_id       = models.UUIDField(null=True, blank=True)
    device_key_id   = models.UUIDField(null=True, blank=True)
    session_id      = models.UUIDField(null=True, blank=True)
    challenge_id    = models.UUIDField(null=True, blank=True)
    action          = models.CharField(max_length=100, choices=Action.choices)
    result          = models.CharField(max_length=10, choices=Result.choices)
    failure_reason  = models.CharField(max_length=255, null=True, blank=True)
    created_at      = models.DateTimeField(auto_now_add=True)
    metadata        = models.JSONField(null=True, blank=True)

    class Meta:
        db_table = 'key_usage_log'
        managed  = False  # no FK — immutable log
        ordering = ['-created_at']
        
    def __str__(self):
        return f"KeyUsage {self.id} — {self.action} ({self.result})"

