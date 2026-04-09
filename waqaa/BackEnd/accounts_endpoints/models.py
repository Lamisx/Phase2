import uuid
from django.db import models
from django.core.exceptions import ValidationError

# user
class WaqaUser(models.Model):
    STATUS_CHOICES = [('active', 'Active'), ('suspended', 'Suspended'), ('deleted', 'Deleted')]

    id               = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    username         = models.CharField(max_length=150,null=False, blank=False, unique=True)
    display_name     = models.CharField(max_length=200,null=False, blank=False)
    email            = models.CharField(max_length=254,null=True, blank=True,unique=True)
    phone            = models.CharField(max_length=20,null=False, blank=False,unique=True)
    national_id_hmac = models.CharField(max_length=128,null=False, blank=False,unique=True)
    status           = models.CharField(max_length=20,default='active', choices=STATUS_CHOICES)
    created_at       = models.DateTimeField(auto_now_add=True)
    updated_at       = models.DateTimeField(auto_now=True)
    password_hash = models.TextField(null=False, blank=False)

    class Meta:
        db_table = 'users'
        indexes = [
            models.Index(fields=['username']),
            models.Index(fields=['phone']),
            models.Index(fields=['email']),
            models.Index(fields=['national_id_hmac']),
            models.Index(fields=['status']),
        ]
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
        constraints = [
        models.UniqueConstraint(
            fields=['primary_user', 'delegate_user'],
            name='unique_primary_delegate_pair'
        )
    ]
    def clean(self):
        if self.primary_user == self.delegate_user:
            raise ValidationError("A user cannot delegate themselves.")

    def __str__(self):
        return f"{self.primary_user} → {self.delegate_user}"
