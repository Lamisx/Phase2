"""
Device services — business logic separated from views.

Responsibilities:
    DeviceService          — create, list, revoke devices.
    DeviceKeyService       — register, list, revoke device keys.
    AccessDecisionService  — quick yes/no access checks.

All write operations are wrapped in @transaction.atomic and use
select_for_update where concurrent writes are possible.
"""
from typing import Optional

from django.db import IntegrityError, transaction
from django.utils import timezone
from rest_framework.exceptions import NotFound, ValidationError

from organization_endpoints.models import Organization

from .models import Device, DeviceKey, DeviceRevocationLog


# ============================================================
# DeviceService
# ============================================================
class DeviceService:
    """Owns the Device lifecycle (create, list, revoke)."""

    # ----------------------------------------------------------------
    # Read helpers
    # ----------------------------------------------------------------
    @staticmethod
    def find_existing_active_device(*, user, app_instance_id) -> Optional[Device]:
        """Return an active device for this (user, app_instance_id), or None.

        Used for idempotent device registration — if the same app instance
        registers twice, we hand back the existing device.
        """
        if not app_instance_id:
            return None
        return Device.objects.filter(
            user=user,
            app_instance_id=app_instance_id,
            is_active=True,
        ).first()

    @staticmethod
    def list_user_devices(*, user):
        """Return active devices belonging to user, newest first."""
        return (
            Device.objects
            .filter(user=user, is_active=True)
            .order_by("-created_at")
        )

    # ----------------------------------------------------------------
    # Write operations
    # ----------------------------------------------------------------
    @staticmethod
    @transaction.atomic
    def create_device(*, user, platform, label=None, app_instance_id=None) -> Device:
        """Create a new device for user.

        The first active device for a user becomes the primary device.
        The unique-primary-per-user constraint guards against races.

        Raises ValidationError on primary conflict (extremely rare —
        only if two concurrent requests both try to claim primary).
        """
        # The first active device becomes primary.
        has_primary = Device.objects.filter(
            user=user,
            is_primary_device=True,
            is_active=True,
        ).exists()

        try:
            return Device.objects.create(
                user=user,
                label=label,
                platform=platform,
                app_instance_id=app_instance_id,
                is_primary_device=not has_primary,
            )
        except IntegrityError:
            raise ValidationError({"error": "PRIMARY_DEVICE_CONFLICT"})

    @staticmethod
    @transaction.atomic
    def revoke_device(*, device_id, user, reason=None) -> Device:
        """Revoke a device owned by user.

        - Locks the row to serialize concurrent revocations.
        - Promotes another device to primary if this was the primary.
        - Revokes all active keys on this device.
        - Writes an immutable audit log entry.

        Raises:
            NotFound — device doesn't exist or isn't owned by user.
            ValidationError — device is already revoked.
        """
        try:
            device = (
                Device.objects
                .select_for_update()
                .get(id=device_id, user=user)
            )
        except Device.DoesNotExist:
            raise NotFound({"error": "DEVICE_NOT_FOUND"})

        if not device.is_active:
            raise ValidationError({"error": "DEVICE_ALREADY_REVOKED"})

        # If we're revoking the primary, promote the oldest active replacement.
        if device.is_primary_device:
            replacement = (
                Device.objects
                .filter(
                    user=user,
                    is_active=True,
                    is_primary_device=False,
                )
                .exclude(id=device.id)
                .order_by("created_at")
                .first()
            )
            if replacement:
                replacement.is_primary_device = True
                replacement.save(update_fields=["is_primary_device", "updated_at"])

        device.is_active = False
        device.is_primary_device = False
        device.save(update_fields=["is_active", "is_primary_device", "updated_at"])

        # Revoke all active keys belonging to this device.
        DeviceKey.objects.filter(device=device, is_active=True).update(
            is_active=False,
            revoked_at=timezone.now(),
            revocation_reason="device_revoked",
        )

        # Immutable audit log.
        DeviceRevocationLog.objects.create(
            device_id=device.id,
            user_id=device.user_id,
            revoked_by_actor_type=DeviceRevocationLog.ACTOR_USER,
            revoked_by_actor_id=user.id,
            reason=reason or "device_revoked",
        )

        return device


# ============================================================
# DeviceKeyService
# ============================================================
class DeviceKeyService:
    """Owns the DeviceKey lifecycle (register, list, revoke)."""

    @staticmethod
    @transaction.atomic
    def register_key(*, user, device_id, organization_id, public_key,
                     algorithm, key_format, key_purpose) -> DeviceKey:
        """Register a new public key for (device, organization, key_purpose).

        If an active key already exists for the same scope, it is
        rotated out (deactivated with reason "key_rotated") before the
        new one is stored. This keeps the unique-active constraint happy
        and gives a clean audit trail of key rotation.

        Raises:
            NotFound — device or organization missing, or device not
                       owned/active.
        """
        try:
            device = (
                Device.objects
                .select_for_update()
                .get(id=device_id, user=user, is_active=True)
            )
        except Device.DoesNotExist:
            raise NotFound({"error": "DEVICE_NOT_FOUND"})

        try:
            organization = Organization.objects.get(id=organization_id)
        except Organization.DoesNotExist:
            raise NotFound({"error": "ORG_NOT_FOUND"})

        # Rotate out any existing active key with the same scope.
        DeviceKey.objects.filter(
            device=device,
            organization=organization,
            key_purpose=key_purpose,
            is_active=True,
        ).update(
            is_active=False,
            revoked_at=timezone.now(),
            revocation_reason="key_rotated",
        )

        return DeviceKey.objects.create(
            device=device,
            organization=organization,
            key_purpose=key_purpose,
            algorithm=algorithm,
            key_format=key_format,
            public_key=public_key,
            is_active=True,
        )

    @staticmethod
    def list_device_keys(*, user, device_id):
        """List active keys for one of the caller's devices.

        Raises NotFound if the device doesn't exist or isn't owned.
        """
        try:
            device = Device.objects.get(
                id=device_id,
                user=user,
                is_active=True,
            )
        except Device.DoesNotExist:
            raise NotFound({"error": "DEVICE_NOT_FOUND"})

        return (
            DeviceKey.objects
            .filter(device=device, is_active=True)
            .select_related("organization", "device")
            .order_by("-created_at")
        )

    @staticmethod
    @transaction.atomic
    def revoke_key(*, user, device_key_id, reason=None) -> DeviceKey:
        """Revoke a single device key (without revoking the whole device).

        Raises:
            NotFound — key doesn't exist or isn't on a device owned by user.
            ValidationError — key is already revoked.
        """
        try:
            device_key = (
                DeviceKey.objects
                .select_related("device")
                .select_for_update()
                .get(id=device_key_id, device__user=user)
            )
        except DeviceKey.DoesNotExist:
            raise NotFound({"error": "DEVICE_KEY_NOT_FOUND"})

        if not device_key.is_active:
            raise ValidationError({"error": "DEVICE_KEY_ALREADY_REVOKED"})

        device_key.is_active = False
        device_key.revoked_at = timezone.now()
        device_key.revocation_reason = reason or "revoked_by_api"
        device_key.save(update_fields=["is_active", "revoked_at", "revocation_reason"])

        return device_key


# ============================================================
# AccessDecisionService
# ============================================================
class AccessDecisionService:
    """Quick yes/no: does the user's device have a valid key for this org?

    Used by clients as a sanity check before initiating a verification flow.
    """

    GRANTED = "granted"
    DENIED = "denied"
    UNKNOWN_DEVICE = "unknown_device"

    @staticmethod
    def evaluate(*, user, device_id, organization_id) -> str:
        """Return one of: GRANTED, DENIED, UNKNOWN_DEVICE."""
        try:
            device = Device.objects.get(
                id=device_id,
                user=user,
                is_active=True,
            )
        except Device.DoesNotExist:
            return AccessDecisionService.UNKNOWN_DEVICE

        has_valid_key = DeviceKey.objects.filter(
            device=device,
            organization_id=organization_id,
            is_active=True,
        ).exists()

        return (
            AccessDecisionService.GRANTED
            if has_valid_key
            else AccessDecisionService.DENIED
        )