import uuid
from django.db import models
from django.contrib.postgres.fields import ArrayField

from accounts_endpoints.models import WaqaUser



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

# ============================================================
# Organization API Key
# ============================================================
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
# Organization User
# ============================================================

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
            ('organization', 'user'),# u cant have d and o and p two times...
        ]

    def __str__(self):
        return f"{self.organization.name} — {self.external_user_ref}"

