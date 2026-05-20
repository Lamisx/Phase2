"""
Organization models.
 
- Organization: tenant / customer that consumes the verification API.
- OrganizationApiKey: machine-to-machine credential bound to an Organization.
- OrganizationUser: links an AccountUser to an Organization with a role.
 
All cross-app FKs use settings.AUTH_USER_MODEL so they remain correct
regardless of whether the user model lives in `accounts_endpoints`,
`account`, or any other label.
"""
import uuid
 
from django.conf import settings
from django.contrib.postgres.fields import ArrayField
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
 
 
# ============================================================
# Soft-delete manager
# ============================================================
class ActiveManager(models.Manager):
    """Returns only rows where deleted_at IS NULL."""
 
    def get_queryset(self):
        return super().get_queryset().filter(deleted_at__isnull=True)
 
 
# ============================================================
# Organization
# ============================================================
class Organization(models.Model):
    STATUS_ACTIVE = "active"
    STATUS_SUSPENDED = "suspended"
    STATUS_PENDING = "pending"
    STATUS_CHOICES = [
        (STATUS_ACTIVE, "Active"),
        (STATUS_SUSPENDED, "Suspended"),
        (STATUS_PENDING, "Pending"),
    ]
 
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, unique=True)
    status = models.CharField(
        max_length=20,
        default=STATUS_ACTIVE,
        choices=STATUS_CHOICES,
        db_index=True,
    )
 
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name="created_organizations",
    )
 
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
 
    class Meta:
        db_table = "organizations"
 
    def __str__(self):
        return self.name
 
 
# ============================================================
# Organization API Key
# ============================================================
class OrganizationApiKey(models.Model):
    """API key issued to an Organization.
 
    `key_hash` is the HMAC-SHA256 hex of the plaintext key (see
    core.utils_crypto.hash_api_key). Plaintext is shown to the org once
    at creation and never persisted.
    """
 
    # Allowed scope strings. Not a Django `choices` (no display labels) —
    # used by clean() to reject unknown values.
    SCOPE_SESSION_CREATE = "session:create"
    SCOPE_SESSION_READ = "session:read"
    SCOPE_SESSION_CANCEL = "session:cancel"
    SCOPE_AUDIT_READ = "audit:read"
    SCOPE_DEVICE_REVOKE = "device:revoke"
 
    ALLOWED_SCOPES = (
        SCOPE_SESSION_CREATE,
        SCOPE_SESSION_READ,
        SCOPE_SESSION_CANCEL,
        SCOPE_AUDIT_READ,
        SCOPE_DEVICE_REVOKE,
    )
 
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="api_keys",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name="created_api_keys",
    )
 
    # 128 chars supports both SHA-256 (64) and SHA-512 (128) hex digests.
    key_hash = models.CharField(max_length=128, unique=True)
    label = models.CharField(max_length=255, null=True, blank=True)
    scopes = ArrayField(models.CharField(max_length=50), default=list)
 
    is_active = models.BooleanField(default=True)
    rate_limit_per_minute = models.IntegerField(default=60)
    allowed_ips = ArrayField(
        models.GenericIPAddressField(),
        null=True, blank=True,
    )
 
    revoked_at = models.DateTimeField(null=True, blank=True)
    last_used_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
 
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
 
    class Meta:
        db_table = "organization_api_keys"
        indexes = [
            models.Index(fields=["organization", "is_active"]),
            models.Index(fields=["key_hash"])
        ]
        constraints = [
            models.CheckConstraint(
                condition=~Q(scopes=[]),
                name="orgapikey_scopes_not_empty",
            ),
            models.UniqueConstraint(
                fields=["organization", "label"],
                condition=~Q(label=None),
                name="orgapikey_unique_label_per_org",
            ),
        ]
 
    def __str__(self):
        return f"{self.organization.name} — {self.label or self.id}"
 
    def clean(self):
        """Validate scopes. Call full_clean() explicitly when needed
        (e.g. from a service); we do NOT auto-clean inside save() to keep
        bulk operations safe."""
        if not self.scopes:
            raise ValidationError({"scopes": "Scopes cannot be empty."})
        for scope in self.scopes:
            if scope not in self.ALLOWED_SCOPES:
                raise ValidationError({"scopes": f"Invalid scope: {scope}"})
 
 
# ============================================================
# Organization User
# ============================================================
class OrganizationUser(models.Model):
    """Links an AccountUser to an Organization with a role."""
 
    STATUS_LINKED = "linked"
    STATUS_PENDING = "pending"
    STATUS_SUSPENDED = "suspended"
    STATUS_UNLINKED = "unlinked"
    STATUS_CHOICES = [
        (STATUS_LINKED, "Linked"),
        (STATUS_PENDING, "Pending"),
        (STATUS_SUSPENDED, "Suspended"),
        (STATUS_UNLINKED, "Unlinked"),
    ]
 
    ROLE_ADMIN = "admin"
    ROLE_MEMBER = "member"
    ROLE_VIEWER = "viewer"
    ROLE_CHOICES = [
        (ROLE_ADMIN, "Admin"),
        (ROLE_MEMBER, "Member"),
        (ROLE_VIEWER, "Viewer"),
    ]
 
    PROVIDER_INTERNAL = "internal"
    PROVIDER_GOOGLE = "google"
    PROVIDER_APPLE = "apple"
    PROVIDER_CHOICES = [
        (PROVIDER_INTERNAL, "Internal"),
        (PROVIDER_GOOGLE, "Google"),
        (PROVIDER_APPLE, "Apple"),
    ]
 
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="org_users",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="org_links",
    )
    linked_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name="linked_users",
    )
 
    external_provider = models.CharField(
        max_length=50,
        choices=PROVIDER_CHOICES,
        default=PROVIDER_INTERNAL,
    )
    external_user_ref = models.CharField(max_length=255)
 
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default=ROLE_MEMBER,
        db_index=True,
    )
    status = models.CharField(
        max_length=20,
        default=STATUS_LINKED,
        choices=STATUS_CHOICES,
        db_index=True,
    )
 
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
 
    objects = ActiveManager()       # excludes soft-deleted rows
    all_objects = models.Manager()  # includes everything
 
    class Meta:
        db_table = "organization_users"
        unique_together = [
            ("organization", "external_user_ref"),
            ("organization", "user"),
        ]
        indexes = [
            models.Index(fields=["organization", "user"]),
            models.Index(fields=["external_user_ref"]),
        ]
 
    def __str__(self):
        return f"{self.organization.name} — {self.external_user_ref}"