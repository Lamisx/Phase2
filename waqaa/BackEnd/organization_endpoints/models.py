import uuid
from django.db import models
from django.contrib.postgres.fields import ArrayField

from accounts_endpoints.models import WaqaUser
from django.core.exceptions import ValidationError
from django.db.models import Q

class ActiveManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(deleted_at__isnull=True)
# ============================================================
# Organization
# ============================================================

class Organization(models.Model):
    STATUS_CHOICES = [
    ('active', 'Active'),
    ('suspended', 'Suspended'),
    ('pending', 'Pending'),
]
    created_by = models.ForeignKey(
    WaqaUser,
    null=True,
    on_delete=models.SET_NULL,
    related_name='created_organizations'
)
    id         = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, unique=True)
    status = models.CharField(
        max_length=20,
        default='active',
        choices=STATUS_CHOICES,
        db_index=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'organizations'

    def __str__(self):
        return self.name

# ============================================================
# Organization API Key
# ============================================================

class OrganizationApiKey(models.Model):
    SCOPE_CHOICES = [
        'session:create', 'session:read', 'session:cancel',
        'audit:read', 'device:revoke'
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    organization = models.ForeignKey(
        'Organization',
        on_delete=models.CASCADE,
        related_name='api_keys'
    )
    created_by = models.ForeignKey(
        WaqaUser,
        null=True,
        on_delete=models.SET_NULL,
        related_name='created_api_keys'
    )
    updated_by = models.ForeignKey(
        WaqaUser,
        null=True,
        on_delete=models.SET_NULL,
        related_name='updated_api_keys'
    )

    key_hash = models.CharField(max_length=64, unique=True)
    label = models.CharField(max_length=255, null=True, blank=True)
    scopes = ArrayField(
        models.CharField(max_length=50),
        default=list
    )

    is_active = models.BooleanField(default=True)

    # 🔐 إضافات الأمان
    rate_limit_per_minute = models.IntegerField(default=10)
    total_requests = models.IntegerField(default=0)
    allowed_ips = ArrayField(models.GenericIPAddressField(), null=True, blank=True)
    revoked_at = models.DateTimeField(null=True, blank=True)

    last_used_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'organization_api_keys'

        indexes = [
            models.Index(fields=['organization']),
            models.Index(fields=['key_hash']),
            models.Index(fields=['created_by']),
            models.Index(fields=['is_active']),
        ]

        constraints = [
            models.CheckConstraint(
                check=~models.Q(scopes=[]),
                name='scopes_not_empty'
            ),

            models.UniqueConstraint(
                fields=['organization', 'label'],
                condition=~Q(label=None),
                name='unique_label_per_org'
            )
        ]
      

    def __str__(self):
        return f"{self.organization.name} — {self.label or self.id}"

    # ✅ Validation للـ scopes
    def clean(self):
        if not self.scopes:
            raise ValidationError("Scopes cannot be empty")

        for scope in self.scopes:
            if scope not in self.SCOPE_CHOICES:
                raise ValidationError(f"Invalid scope: {scope}")
    # ✅ ربط validation بالحفظ
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
# ============================================================
# Organization User
# ============================================================

class OrganizationUser(models.Model):
    STATUS_CHOICES = [
        ('linked', 'Linked'), ('pending', 'Pending'),
        ('suspended', 'Suspended'), ('unlinked', 'Unlinked')
    ]

    EXTERNAL_PROVIDER_CHOICES = [
        ('internal', 'Internal'),
        ('google', 'Google'),
        ('apple', 'Apple'),
    ]

    linked_by = models.ForeignKey(
    WaqaUser,
    null=True,
    on_delete=models.SET_NULL,
    related_name='linked_users'
)
    
    id                = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization      = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='org_users')
    user              = models.ForeignKey(WaqaUser, on_delete=models.CASCADE, related_name='org_links')

    external_provider = models.CharField(
        max_length=50,
        choices=EXTERNAL_PROVIDER_CHOICES
    )

    external_user_ref = models.CharField(max_length=255)

    status = models.CharField(
    max_length=20,
    default='linked',
    choices=STATUS_CHOICES,
    db_index=True
)
    created_at        = models.DateTimeField(auto_now_add=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    objects = ActiveManager()     # يرجع فقط غير المحذوف
    all_objects = models.Manager()  # يرجع الكل


    class Meta:
        db_table = 'organization_users'
        unique_together = [
            ('organization', 'external_user_ref'),
            ('organization', 'user'),
        ]
        indexes = [
            models.Index(fields=['organization', 'user']),
            models.Index(fields=['external_user_ref']),
            models.Index(fields=['user']),  # 👈 هذا هو التعديل
        ]

    def __str__(self):
        return f"{self.organization.name} — {self.external_user_ref}"
    
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('member', 'Member'),
        ('viewer', 'Viewer')
    ]

    role = models.CharField(
    max_length=20,
    choices=ROLE_CHOICES,
    default='member',
    db_index=True
)
#====================
