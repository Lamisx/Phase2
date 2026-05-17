"""
Verification services — business logic for the verification flow.

Organization:
    TrustEngine                 — evaluates whether a verified device's
                                  owner is allowed to perform the operation.
    VerificationService         — create sessions, verify signatures,
                                  cancel sessions, verify decision tokens.
    write_audit / write_key_usage — best-effort audit logging.
"""
import base64
import hashlib
import secrets
from datetime import timedelta
from typing import Optional, Tuple

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric import ed25519
from django.conf import settings
from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from accounts_endpoints.models import UserDelegation
from devices_endpoints.models import Device, DeviceKey

from .models import (
    AuditLog,
    KeyUsageLog,
    VerificationChallenge,
    VerificationSession,
)


# ============================================================
# Constants
# ============================================================
SESSION_TTL_MINUTES = getattr(settings, "VERIFICATION_SESSION_TTL_MINUTES", 5)
CHALLENGE_TTL_SECONDS = getattr(settings, "VERIFICATION_CHALLENGE_TTL_SECONDS", 120)


class DenialReason:
    DEVICE_NOT_FOUND = "device_not_found"
    DEVICE_NOT_TRUSTED = "device_not_trusted"
    DEVICE_INACTIVE = "device_inactive"
    DEVICE_NOT_BOUND_TO_USER = "device_not_bound_to_user"
    USER_NOT_FOUND = "user_not_found"
    DELEGATE_NOT_AUTHORIZED = "delegate_not_authorized"
    OPERATION_REQUIRES_PRIMARY = "operation_requires_primary"
    NO_REGISTERED_KEY = "no_registered_key_for_organization"


# Operations that only the primary user can authorize.
PRIMARY_ONLY_OPERATIONS = {
    VerificationSession.OperationType.ADD_DELEGATE,
    VerificationSession.OperationType.REMOVE_DELEGATE,
}


# ============================================================
# Small helpers
# ============================================================
def generate_nonce() -> str:
    return secrets.token_urlsafe(32)


def generate_challenge_bytes_hex() -> str:
    """32 random bytes encoded as hex (signing material)."""
    return secrets.token_bytes(32).hex()


def sha256_hex(data) -> str:
    if isinstance(data, str):
        data = data.encode("utf-8")
    return hashlib.sha256(data).hexdigest()


# ============================================================
# Audit logging (best-effort; never raises)
# ============================================================
def write_audit(*, organization_id=None, session_id=None, device_id=None,
                actor_type: str, actor_id=None, action: str, result: str,
                ip_address: Optional[str] = None,
                user_agent: Optional[str] = None,
                metadata: Optional[dict] = None) -> None:
    try:
        AuditLog.objects.create(
            organization_id=organization_id,
            session_id=session_id,
            device_id=device_id,
            actor_type=actor_type,
            actor_id=actor_id,
            action=action,
            result=result,
            ip_address=ip_address,
            user_agent=user_agent,
            metadata=metadata or {},
        )
    except Exception:
        # Audit must never break the request path.
        pass


def write_key_usage(**kwargs) -> None:
    try:
        KeyUsageLog.objects.create(**kwargs)
    except Exception:
        pass


# ============================================================
# Trust Engine
# ============================================================
class TrustEngine:
    """Decides whether a verified device + user can authorize an operation."""

    @staticmethod
    def evaluate(
        *,
        org_user,              # OrganizationUser (has .user → AccountUser)
        target_device: Device, # device that just verified
        operation_type: str,
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """Return (allowed, denial_reason, actor_type).

        - allowed: True if the (device, user, operation) triple is authorized.
        - denial_reason: a DenialReason value when not allowed; otherwise None.
        - actor_type: PRIMARY or DELEGATE on success; otherwise None.
        """
        if target_device is None:
            return False, DenialReason.DEVICE_NOT_FOUND, None

        if not target_device.is_active:
            return False, DenialReason.DEVICE_INACTIVE, None

        if not target_device.is_trusted:
            return False, DenialReason.DEVICE_NOT_TRUSTED, None

        device_owner = target_device.user
        if device_owner is None:
            return False, DenialReason.DEVICE_NOT_BOUND_TO_USER, None

        if org_user is None or org_user.user is None:
            return False, DenialReason.USER_NOT_FOUND, None

        primary_user = org_user.user

        # Case 1: device belongs to the primary user themselves.
        if device_owner.id == primary_user.id:
            return True, None, VerificationSession.ActorType.PRIMARY

        # Case 2: device belongs to a delegate of the primary user.
        delegation = TrustEngine._find_active_delegation(
            owner=primary_user,
            delegate=device_owner,
        )
        if delegation is None:
            return False, DenialReason.DELEGATE_NOT_AUTHORIZED, None

        # Some operations are too sensitive to delegate.
        if operation_type in PRIMARY_ONLY_OPERATIONS:
            return False, DenialReason.OPERATION_REQUIRES_PRIMARY, None

        return True, None, VerificationSession.ActorType.DELEGATE

    @staticmethod
    def _find_active_delegation(*, owner, delegate) -> Optional[UserDelegation]:
        now = timezone.now()
        return (
            UserDelegation.objects
            .filter(
                owner_account=owner,
                delegated_account=delegate,
                status=UserDelegation.STATUS_ACTIVE,
            )
            .filter(Q(expires_at__isnull=True) | Q(expires_at__gt=now))
            .first()
        )


# ============================================================
# Cryptography helpers (Ed25519 + base64)
# ============================================================
def _load_device_public_key(device_key: DeviceKey) -> ed25519.Ed25519PublicKey:
    """Load an Ed25519 public key from a DeviceKey row.

    Only Ed25519 / RAW (base64) is supported by register_device_key, so
    that's all we handle here.
    """
    if device_key.algorithm != "Ed25519" or device_key.key_format != "RAW":
        raise ValueError("unsupported_key_format")

    try:
        raw = base64.b64decode((device_key.public_key or "").strip(), validate=True)
    except Exception as exc:
        raise ValueError("invalid_public_key_encoding") from exc

    if len(raw) != 32:
        raise ValueError("invalid_ed25519_public_key_length")

    return ed25519.Ed25519PublicKey.from_public_bytes(raw)


def _verify_ed25519(public_key: ed25519.Ed25519PublicKey,
                    message: bytes, signature: bytes) -> bool:
    try:
        public_key.verify(signature, message)
        return True
    except InvalidSignature:
        return False
    except Exception:
        return False


# ============================================================
# Verification Service
# ============================================================
class VerificationService:
    """Owns the verification session lifecycle."""

    # ----------------------------------------------------------------
    # Create
    # ----------------------------------------------------------------
    @staticmethod
    @transaction.atomic
    def create_session_and_issue_challenge(
        *,
        organization,
        org_user,
        org_operation_ref: str,
        operation_type: str,
        operation_hash: Optional[str] = None,
        operation_payload_encrypted: Optional[str] = None,
        client_ip: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> Tuple[VerificationSession, VerificationChallenge]:
        """Create a session and its first challenge atomically."""
        expires_at = timezone.now() + timedelta(minutes=SESSION_TTL_MINUTES)

        session = VerificationSession.objects.create(
            organization=organization,
            org_user=org_user,
            org_operation_ref=org_operation_ref,
            operation_type=operation_type,
            operation_hash=operation_hash,
            operation_payload_encrypted=operation_payload_encrypted,
            nonce=generate_nonce(),
            client_ip=client_ip,
            user_agent=user_agent,
            expires_at=expires_at,
            status=VerificationSession.Status.PENDING,
        )

        challenge = VerificationChallenge.objects.create(
            session=session,
            challenge_bytes=generate_challenge_bytes_hex(),
            attempt_number=1,
            is_active=True,
            is_used=False,
            expires_at=timezone.now() + timedelta(seconds=CHALLENGE_TTL_SECONDS),
        )

        session.attempt_count = 1
        session.status = VerificationSession.Status.CHALLENGE_ISSUED
        session.save(update_fields=["attempt_count", "status"])

        return session, challenge

    # ----------------------------------------------------------------
    # Verify (device-side signature)
    # ----------------------------------------------------------------
    @staticmethod
    @transaction.atomic
    def verify_signature_and_decide(
        *,
        session_id,
        device_id,
        signature_b64: str,
    ) -> Tuple[VerificationSession, Optional[str]]:
        """Verify the device's signature over the active challenge and
        decide whether to authorize the operation.

        Returns (session, decision_token).
        decision_token is None on denial or non-verified outcome.

        Raises ValueError(reason) for early errors (session not found,
        expired, wrong state, no active challenge, etc).
        """
        # 1) Load + lock session
        try:
            session = (
                VerificationSession.objects
                .select_for_update()
                .select_related("organization", "org_user", "org_user__user")
                .get(id=session_id)
            )
        except VerificationSession.DoesNotExist:
            raise ValueError("session_not_found")

        if session.is_expired:
            session.update_expired_status()
            raise ValueError("session_expired")

        if session.status != VerificationSession.Status.CHALLENGE_ISSUED:
            raise ValueError("invalid_session_status")

        # 2) Find the latest active, unused challenge
        challenge = (
            VerificationChallenge.objects
            .select_for_update()
            .filter(session=session, is_active=True, is_used=False)
            .order_by("-attempt_number")
            .first()
        )
        if challenge is None:
            raise ValueError("no_active_challenge")

        if challenge.is_expired:
            challenge.is_active = False
            challenge.save(update_fields=["is_active"])
            raise ValueError("challenge_expired")

        # 3) Load device
        try:
            device = Device.objects.select_related("user").get(id=device_id)
        except Device.DoesNotExist:
            raise ValueError("device_not_found")

        # 4) Find the device's active key for THIS organization (auth scope)
        device_key = device.get_active_key(
            organization=session.organization,
            key_purpose=DeviceKey.PURPOSE_AUTH,
        )
        if device_key is None:
            write_key_usage(
                organization_id=session.organization_id,
                device_id=device.id,
                session_id=session.id,
                challenge_id=challenge.id,
                action=KeyUsageLog.Action.VERIFY,
                result=KeyUsageLog.Result.FAIL,
                failure_reason=DenialReason.NO_REGISTERED_KEY,
            )
            raise ValueError(DenialReason.NO_REGISTERED_KEY)

        # 5) Decode signature
        try:
            signature_bytes = base64.b64decode(signature_b64, validate=True)
        except Exception:
            write_key_usage(
                organization_id=session.organization_id,
                device_id=device.id,
                device_key_id=device_key.id,
                session_id=session.id,
                challenge_id=challenge.id,
                action=KeyUsageLog.Action.VERIFY,
                result=KeyUsageLog.Result.FAIL,
                failure_reason="invalid_signature_encoding",
            )
            _consume_challenge_and_count(session, challenge)
            raise ValueError("invalid_signature_encoding")

        # 6) Load public key
        try:
            public_key = _load_device_public_key(device_key)
        except ValueError as exc:
            write_key_usage(
                organization_id=session.organization_id,
                device_id=device.id,
                device_key_id=device_key.id,
                session_id=session.id,
                challenge_id=challenge.id,
                action=KeyUsageLog.Action.VERIFY,
                result=KeyUsageLog.Result.FAIL,
                failure_reason=str(exc),
            )
            raise ValueError("public_key_unavailable")

        # 7) Verify signature over challenge bytes
        message = bytes.fromhex(challenge.challenge_bytes)
        if not _verify_ed25519(public_key, message, signature_bytes):
            write_key_usage(
                organization_id=session.organization_id,
                device_id=device.id,
                device_key_id=device_key.id,
                session_id=session.id,
                challenge_id=challenge.id,
                action=KeyUsageLog.Action.VERIFY,
                result=KeyUsageLog.Result.FAIL,
                failure_reason="invalid_signature",
            )
            _consume_challenge_and_count(session, challenge)
            raise ValueError("invalid_signature")

        # Signature is valid — now evaluate trust.
        challenge.mark_as_used(commit=True)

        # Stamp last_used_at on the device key.
        DeviceKey.objects.filter(pk=device_key.pk).update(last_used_at=timezone.now())

        allowed, denial_reason, actor_type = TrustEngine.evaluate(
            org_user=session.org_user,
            target_device=device,
            operation_type=session.operation_type,
        )

        # 8a) Denied
        if not allowed:
            session.status = VerificationSession.Status.DENIED
            session.failure_reason = denial_reason
            session.device = device
            session.save(update_fields=["status", "failure_reason", "device"])
            write_key_usage(
                organization_id=session.organization_id,
                device_id=device.id,
                device_key_id=device_key.id,
                session_id=session.id,
                challenge_id=challenge.id,
                action=KeyUsageLog.Action.VERIFY,
                result=KeyUsageLog.Result.OK,
                failure_reason=denial_reason,
                metadata={"trust_decision": "denied"},
            )
            return session, None

        # 8b) Verified — generate decision token
        decision_token = secrets.token_urlsafe(48)
        verified_by_user = (
            session.org_user.user
            if actor_type == VerificationSession.ActorType.PRIMARY
            else device.user
        )

        session.status = VerificationSession.Status.VERIFIED
        session.verified_at = timezone.now()
        session.device = device
        session.verified_by_actor_type = actor_type
        session.verified_by_user = verified_by_user
        session.decision_token_hash = sha256_hex(decision_token)
        session.save(update_fields=[
            "status", "verified_at", "device",
            "verified_by_actor_type", "verified_by_user",
            "decision_token_hash",
        ])
        write_key_usage(
            organization_id=session.organization_id,
            device_id=device.id,
            device_key_id=device_key.id,
            session_id=session.id,
            challenge_id=challenge.id,
            action=KeyUsageLog.Action.VERIFY,
            result=KeyUsageLog.Result.OK,
            metadata={"trust_decision": "verified", "actor_type": actor_type},
        )
        return session, decision_token

    # ----------------------------------------------------------------
    # Cancel
    # ----------------------------------------------------------------
    @staticmethod
    @transaction.atomic
    def cancel_session(*, session: VerificationSession,
                       reason: str = "cancelled_by_org") -> bool:
        """Cancel a non-final session. Returns False if already final."""
        session = (
            VerificationSession.objects
            .select_for_update()
            .get(pk=session.pk)
        )
        if session.is_final:
            return False
        session.status = VerificationSession.Status.CANCELLED
        session.failure_reason = reason
        session.save(update_fields=["status", "failure_reason"])
        return True

    # ----------------------------------------------------------------
    # Decision token verification (organization callback)
    # ----------------------------------------------------------------
    @staticmethod
    def verify_decision_token(*, organization, session_id, token: str) -> bool:
        """Check that a decision_token matches a VERIFIED session for this org."""
        if not token:
            return False
        try:
            session = VerificationSession.objects.get(
                id=session_id,
                organization=organization,
            )
        except VerificationSession.DoesNotExist:
            return False

        if session.status != VerificationSession.Status.VERIFIED:
            return False
        if not session.decision_token_hash:
            return False

        return secrets.compare_digest(
            session.decision_token_hash,
            sha256_hex(token),
        )


# ============================================================
# Internal helpers
# ============================================================
def _consume_challenge_and_count(session: VerificationSession,
                                 challenge: VerificationChallenge) -> None:
    """Mark challenge used + bump attempt_count. Mark session FAILED if exhausted."""
    challenge.mark_as_used(commit=True)
    session.attempt_count = (session.attempt_count or 0) + 1
    update_fields = ["attempt_count"]

    if session.attempts_exhausted:
        session.status = VerificationSession.Status.FAILED
        session.failure_reason = "attempts_exhausted"
        update_fields += ["status", "failure_reason"]

    session.save(update_fields=update_fields)