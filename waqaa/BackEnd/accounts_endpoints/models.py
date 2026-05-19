import uuid
from django.db import models
from django.core.exceptions import ValidationError
from datetime import timedelta
from django.utils import timezone
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from .managers import AccountUserManager


# ============================================================
# Registration Session
# ============================================================

#GOOD architecture ✅
class RegistrationSession(models.Model):
    """AccountUser."""

    STATUS_PENDING = "pending"
    STATUS_IDENTITY_VERIFIED = "identity_verified"
    STATUS_COMPLETED = "completed"
    STATUS_EXPIRED = "expired"
    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_IDENTITY_VERIFIED, "Identity Verified"),
        (STATUS_COMPLETED, "Completed"),
        (STATUS_EXPIRED, "Expired"),
    ]

    ACTIVE_STATUSES = (STATUS_PENDING, STATUS_IDENTITY_VERIFIED)
    FINAL_STATUSES = (STATUS_COMPLETED, STATUS_EXPIRED)
 
    DEFAULT_TTL_MINUTES = 10

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    national_id_hmac = models.CharField(max_length=64, db_index=True)

    username = models.CharField(max_length=20, null=True, blank=True)
    password_hash = models.CharField(max_length=128,  null=True, blank=True)
    display_name = models.CharField(max_length=20, null=True, blank=True)
    phone = models.CharField(max_length=10, null=True, blank=True)
    email = models.EmailField()#change

    status = models.CharField(
        max_length=32, choices=STATUS_CHOICES, default=STATUS_PENDING,
    )

    account = models.ForeignKey(
        "accounts_endpoints.AccountUser",
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name="registration_sessions",
    )

    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "registration_sessions"
        indexes = [
            models.Index(fields=["status", "expires_at"]),
            models.Index(fields=["national_id_hmac", "status"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["national_id_hmac"],
                condition=models.Q(status__in=["pending", "identity_verified"]),
                name="regsession_one_active_per_national_id",
            ),
        ]

    def save(self, *args, **kwargs):
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(minutes=self.DEFAULT_TTL_MINUTES)
        super().save(*args, **kwargs)

    @property
    def is_expired(self) -> bool:
        return timezone.now() >= self.expires_at

    @property
    def is_final(self) -> bool:
        return self.status in self.FINAL_STATUSES

    def __str__(self):
        return f"RegistrationSession {self.id} ({self.status})"



# ============================================================
# Account User✅
# ============================================================
class AccountUser(AbstractBaseUser, PermissionsMixin):

    STATUS_ACTIVE = "active"
    STATUS_SUSPENDED = "suspended"
    STATUS_DELETED = "deleted"
    STATUS_CHOICES = [
        (STATUS_ACTIVE, "Active"),
        (STATUS_SUSPENDED, "Suspended"),
        (STATUS_DELETED, "Deleted"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    username = models.CharField(max_length=150, unique=True)
    display_name = models.CharField(max_length=200)
    email = models.EmailField()#change
    phone = models.CharField(max_length=20, null=True, blank=True, unique=True)
    national_id_hmac = models.CharField(
        max_length=128, null=True, blank=True, unique=True,
    )

    status = models.CharField(
        max_length=20, default=STATUS_ACTIVE, choices=STATUS_CHOICES,
    )

    # حقول Django auth الإلزامية
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = AccountUserManager()

    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = ["display_name"]

    class Meta:
        db_table = "accounts"
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["national_id_hmac"]),
        ]

    def __str__(self):
        return self.username


# ============================================================
# User Delegation ✅
# ============================================================
class UserDelegation(models.Model):

    METHOD_QR = "qr"
    METHOD_OTP = "otp"
    METHOD_CHOICES = [(METHOD_QR, "QR"), (METHOD_OTP, "OTP")]

    STATUS_ACTIVE = "active"
    STATUS_REVOKED = "revoked"
    STATUS_EXPIRED = "expired"
    STATUS_CHOICES = [
        (STATUS_ACTIVE, "Active"),
        (STATUS_REVOKED, "Revoked"),
        (STATUS_EXPIRED, "Expired"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    owner_account = models.ForeignKey(
        "accounts_endpoints.AccountUser",
        on_delete=models.CASCADE,
        related_name="delegations_granted",
    )
    delegated_account = models.ForeignKey(
        "accounts_endpoints.AccountUser",
        on_delete=models.CASCADE,
        related_name="delegations_received",
    )

    delegation_method = models.CharField(max_length=10, choices=METHOD_CHOICES)
    status = models.CharField(
        max_length=20, default=STATUS_ACTIVE, choices=STATUS_CHOICES,
    )

    expires_at = models.DateTimeField(null=True, blank=True)
    revoked_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "user_delegations"
        constraints = [
            # لا يقدر مستخدم يفوّض نفسه — على مستوى DB
            models.CheckConstraint(
                condition=models.Q(owner_account=models.F("delegated_account")),
                name="udel_no_self_delegation",
            ),
            # تفويض نشط واحد فقط لكل زوج (owner, delegated)
            models.UniqueConstraint(
                fields=["owner_account", "delegated_account"],
                condition=models.Q(status="active"),
                name="udel_unique_active",
            ),
        ]
        indexes = [
            models.Index(fields=["owner_account", "status"]),
            models.Index(fields=["delegated_account", "status"]),
        ]

    def clean(self):
        if self.owner_account_id == self.delegated_account_id:
            raise ValidationError("An account cannot delegate to itself.")

    @property
    def is_expired(self) -> bool:
        if self.expires_at is None:
            return False
        return timezone.now() >= self.expires_at

    def __str__(self):
        return f"{self.owner_account_id} → {self.delegated_account_id}"