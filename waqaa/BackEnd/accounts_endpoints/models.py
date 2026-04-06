import uuid
from django.db import models

# user
class WaqaUser(models.Model):
    STATUS_CHOICES = [('active', 'Active'), ('suspended', 'Suspended'), ('deleted', 'Deleted')]

    id               = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    username         = models.TextField(null=True, blank=True, unique=True)
    display_name     = models.TextField(null=True, blank=True)
    email            = models.TextField(null=True, blank=True,unique=True)
    phone            = models.TextField(null=True, blank=True,unique=True)
    national_id_hmac = models.TextField(null=True, blank=True,unique=True)
    status           = models.TextField(default='active', choices=STATUS_CHOICES)
    created_at       = models.DateTimeField(auto_now_add=True)
    updated_at       = models.DateTimeField(auto_now=True)
    password_hash = models.TextField(null=True, blank=True)

    class Meta:
        db_table = 'users'

    def __str__(self):
        return self.username or self.display_name or str(self.id)
    

# Delegated Access
class DelegatedAccess(models.Model):
    ADDED_VIA_CHOICES = [('qr', 'QR'), ('otp', 'OTP')]
    STATUS_CHOICES    = [('active', 'Active'), ('revoked', 'Revoked')]

    id                   = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    primary_user     = models.ForeignKey(WaqaUser, on_delete=models.CASCADE, related_name='delegated_to')
    delegate_user    = models.ForeignKey(WaqaUser, on_delete=models.CASCADE, related_name='delegated_from')
    added_via            = models.TextField(choices=ADDED_VIA_CHOICES)
    status               = models.TextField(default='active', choices=STATUS_CHOICES)
    created_at           = models.DateTimeField(auto_now_add=True)
    revoked_at           = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'delegated_access'
        unique_together = [('primary_user', 'delegate_user')]

    def __str__(self):
        return f"{self.primary_user} → {self.delegate_user}"