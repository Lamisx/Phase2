import base64
import secrets
import hashlib
from datetime import timedelta
from typing import Optional, Tuple
from .authentication import hash_api_key
from django.conf import settings
from django.utils import timezone
from django.db import transaction
from django.db.models import Q
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ed25519, ec
from devices_endpoints.models import Device
from organization_endpoints.models import OrganizationUser
from .models import (
    VerificationSession,
    VerificationChallenge,
    AuditLog,
    KeyUsageLog,
)

# ============================================================
# Constants
# ============================================================
SESSION_TTL_MINUTES = getattr(settings, "VERIFICATION_SESSION_TTL_MINUTES", 5)
CHALLENGE_TTL_SECONDS = getattr(settings, "VERIFICATION_CHALLENGE_TTL_SECONDS", 120)

# ============================================================
# Failure reasons (canonical)
# ============================================================
class DenialReason:
    DEVICE_NOT_FOUND = "device_not_found"
    DEVICE_NOT_TRUSTED = "device_not_trusted"
    DEVICE_INACTIVE = "device_inactive"
    DEVICE_NOT_BOUND_TO_USER = "device_not_bound_to_user"
    USER_NOT_FOUND = "user_not_found"
    DELEGATE_NOT_AUTHORIZED = "delegate_not_authorized"
    DELEGATION_EXPIRED = "delegation_expired"
    OPERATION_REQUIRES_PRIMARY = "operation_requires_primary"
    SESSION_EXPIRED = "session_expired"

PRIMARY_ONLY_OPERATIONS = {
    VerificationSession.OperationType.ADD_DELEGATE,
    VerificationSession.OperationType.REMOVE_DELEGATE,
}

# ============================================================
# Helpers
# ============================================================
def generate_nonce() -> str:
    return secrets.token_urlsafe(32)

def generate_challenge_bytes_hex() -> str:
    """32 random bytes encoded as hex (forensic + signing material)."""
    return secrets.token_bytes(32).hex()

def sha256_hex(data: bytes | str) -> str:
    if isinstance(data, str):
        data = data.encode("utf-8")
    return hashlib.sha256(data).hexdigest()

def get_client_ip(request) -> Optional[str]:
    xff = request.META.get("HTTP_X_FORWARDED_FOR")
    if xff:
        return xff.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")

def get_user_agent(request) -> Optional[str]:
    return request.META.get("HTTP_USER_AGENT", "")[:512] or None

# ============================================================
# Audit logging (best-effort, never raises)
# ============================================================
def write_audit(
    *,
    organization_id=None,
    session_id=None,
    device_id=None,
    actor_type: str,
    actor_id=None,
    action: str,
    result: str,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    metadata: Optional[dict] = None,
):
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
        pass

def write_key_usage(**kwargs):
    try:
        KeyUsageLog.objects.create(**kwargs)
    except Exception:
        pass

# ============================================================
# Decision Engine — server-side trust evaluation
# ============================================================
def evaluate_trust(
    *,
    org_user: OrganizationUser,
    target_device: Device,
    operation_type: str,
) -> Tuple[bool, Optional[str], Optional[str]]:

    if target_device is None:
        return False, DenialReason.DEVICE_NOT_FOUND, None

    if not getattr(target_device, "is_active", True):
        return False, DenialReason.DEVICE_INACTIVE, None

    if not getattr(target_device, "is_trusted", False):
        return False, DenialReason.DEVICE_NOT_TRUSTED, None

    device_owner = (
        getattr(target_device, "waqa_user", None)
        or getattr(target_device, "owner", None)
    )
    if device_owner is None:
        return False, DenialReason.DEVICE_NOT_BOUND_TO_USER, None

    primary_waqa_user = getattr(org_user, "waqa_user", None)
    if primary_waqa_user is None:
        return False, DenialReason.USER_NOT_FOUND, None

    if device_owner.id == primary_waqa_user.id:
        return True, None, VerificationSession.ActorType.PRIMARY

    delegation = _find_active_delegation(
        primary=primary_waqa_user,
        delegate=device_owner,
    )
    if delegation is None:
        return False, DenialReason.DELEGATE_NOT_AUTHORIZED, None

    if operation_type in PRIMARY_ONLY_OPERATIONS:
        return False, DenialReason.OPERATION_REQUIRES_PRIMARY, None

    if not _delegation_permits(delegation, operation_type):
        return False, DenialReason.DELEGATE_NOT_AUTHORIZED, None

    return True, None, VerificationSession.ActorType.DELEGATE

def _find_active_delegation(*, primary, delegate):
    try:
        from accounts_endpoints.models import Delegation
    except ImportError:
        return None

    now = timezone.now()
    return (
        Delegation.objects
        .filter(
            primary_user=primary,
            delegate_user=delegate,
            is_active=True,
        )
        .filter(_q_not_expired(now))
        .first()
    )

def _q_not_expired(now):
    return Q(expires_at__isnull=True) | Q(expires_at__gt=now)

def _delegation_permits(delegation, operation_type: str) -> bool:
    allowed_ops = getattr(delegation, "allowed_operations", None)
    if allowed_ops is None:
        return True
    if hasattr(allowed_ops, "all"):
        return allowed_ops.filter(code=operation_type).exists()
    if isinstance(allowed_ops, (list, tuple, set)):
        return operation_type in allowed_ops
    return False

# ============================================================
# Public-key resolution (supports raw bytes OR PEM)
# ============================================================
def _load_device_public_key(device: Device):

    active_key = getattr(device, "active_key", None)
    if active_key is not None:
        raw = getattr(active_key, "public_key_bytes", None)
        if raw:
            algorithm = (getattr(active_key, "algorithm", "") or "").lower()

            if algorithm in ("ed25519", "eddsa"):
                return ed25519.Ed25519PublicKey.from_public_bytes(raw)
            if algorithm in ("ecdsa", "ecdsa-p256", "ec", "p256", "secp256r1"):
                return ec.EllipticCurvePublicKey.from_encoded_point(
                    ec.SECP256R1(), raw
                )

            if len(raw) == 32:
                return ed25519.Ed25519PublicKey.from_public_bytes(raw)
            if len(raw) == 65 and raw[:1] == b"\x04":
                return ec.EllipticCurvePublicKey.from_encoded_point(
                    ec.SECP256R1(), raw
                )
            raise ValueError("unsupported_raw_public_key_format")

    pem = getattr(device, "public_key", None)
    if pem:
        if isinstance(pem, str):
            pem = pem.encode("utf-8")
        public_key = serialization.load_pem_public_key(pem)
        if isinstance(public_key, ed25519.Ed25519PublicKey):
            return public_key
        if isinstance(public_key, ec.EllipticCurvePublicKey):
            return public_key
        raise ValueError("unsupported_pem_public_key_type")
    raise ValueError("device_public_key_missing")

def _verify_signature(public_key, message: bytes, signature: bytes) -> bool:

    try:
        if isinstance(public_key, ed25519.Ed25519PublicKey):
            public_key.verify(signature, message)
            return True
        if isinstance(public_key, ec.EllipticCurvePublicKey):
            public_key.verify(signature, message, ec.ECDSA(hashes.SHA256()))
            return True
    except InvalidSignature:
        return False
    except Exception:
        return False
    return False

# ============================================================
# Session creation + challenge issuance
# ============================================================

@transaction.atomic
def create_session_and_issue_challenge(
    *,
    organization,
    org_user: Optional[OrganizationUser],
    org_operation_ref: str,
    operation_type: str,
    operation_payload_encrypted: Optional[str] = None,
    operation_hash: Optional[str] = None,
    client_ip: Optional[str] = None,
    user_agent: Optional[str] = None,
) -> Tuple[VerificationSession, VerificationChallenge]:

    expires_at = timezone.now() + timedelta(minutes=SESSION_TTL_MINUTES)

    session = VerificationSession.objects.create(
        organization=organization,
        org_user=org_user,
        org_operation_ref=org_operation_ref,
        operation_type=operation_type,
        operation_payload_encrypted=operation_payload_encrypted,
        operation_hash=operation_hash,
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

# ============================================================
# Signature verification + decision
# ============================================================

@transaction.atomic
def verify_signature_and_decide(*,session_id,device_id,signature_b64: str,) -> Tuple[VerificationSession, Optional[str]]:
    try:
        session = (
            VerificationSession.objects
            .select_for_update()
            .get(id=session_id)
        )
    except VerificationSession.DoesNotExist:
        raise ValueError("session_not_found")

    if session.is_expired:
        session.update_expired_status()
        raise ValueError("session_expired")

    if session.status != VerificationSession.Status.CHALLENGE_ISSUED:
        raise ValueError("invalid_session_status")

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

    try:
        device = Device.objects.get(id=device_id)
    except Device.DoesNotExist:
        raise ValueError("device_not_found")

    try:
        signature_bytes = base64.b64decode(signature_b64, validate=True)
    except Exception:
        write_key_usage(
            organization_id=session.organization_id,
            device_id=device.id,
            session_id=session.id,
            challenge_id=challenge.id,
            action=KeyUsageLog.Action.VERIFY,
            result=KeyUsageLog.Result.FAIL,
            failure_reason="invalid_signature_encoding",
        )
        _consume_challenge_and_count(session, challenge, "invalid_signature_encoding")
        raise ValueError("invalid_signature_encoding")

    try:
        public_key = _load_device_public_key(device)
    except ValueError as e:
        write_key_usage(
            organization_id=session.organization_id,
            device_id=device.id,
            session_id=session.id,
            challenge_id=challenge.id,
            action=KeyUsageLog.Action.VERIFY,
            result=KeyUsageLog.Result.FAIL,
            failure_reason=str(e),
        )
        raise ValueError("public_key_unavailable")
    
    message = bytes.fromhex(challenge.challenge_bytes)
    is_valid = _verify_signature(public_key, message, signature_bytes)
    if not is_valid:
        write_key_usage(
            organization_id=session.organization_id,
            device_id=device.id,
            device_key_id=getattr(getattr(device, "active_key", None), "id", None),
            session_id=session.id,
            challenge_id=challenge.id,
            action=KeyUsageLog.Action.VERIFY,
            result=KeyUsageLog.Result.FAIL,
            failure_reason="invalid_signature",
        )
        _consume_challenge_and_count(session, challenge, "invalid_signature")
        raise ValueError("invalid_signature")
    allowed, denial_reason, actor_type = evaluate_trust(
        org_user=session.org_user,
        target_device=device,
        operation_type=session.operation_type,
    )

    challenge.mark_as_used(commit=True)
    if not allowed:
        session.status = VerificationSession.Status.DENIED
        session.failure_reason = denial_reason
        session.device = device
        session.save(update_fields=["status", "failure_reason", "device"])
        write_key_usage(
            organization_id=session.organization_id,
            device_id=device.id,
            device_key_id=getattr(getattr(device, "active_key", None), "id", None),
            session_id=session.id,
            challenge_id=challenge.id,
            action=KeyUsageLog.Action.VERIFY,
            result=KeyUsageLog.Result.OK,  
            failure_reason=denial_reason,
            metadata={"trust_decision": "denied"},
        )
        return session, None

    decision_token = secrets.token_urlsafe(48)
    primary_waqa_user = getattr(session.org_user, "waqa_user", None) if session.org_user else None
    if actor_type == VerificationSession.ActorType.PRIMARY:
        verified_by_user = primary_waqa_user
    else:
        verified_by_user = (
            getattr(device, "waqa_user", None)
            or getattr(device, "owner", None)
        )
    session.status = VerificationSession.Status.VERIFIED
    session.verified_at = timezone.now()
    session.device = device
    session.verified_by_actor_type = actor_type
    session.verified_by_user = verified_by_user
    session.decision_token_hash = sha256_hex(decision_token)
    session.save(update_fields=[
        "status",
        "verified_at",
        "device",
        "verified_by_actor_type",
        "verified_by_user",
        "decision_token_hash",
    ])
    write_key_usage(
        organization_id=session.organization_id,
        device_id=device.id,
        device_key_id=getattr(getattr(device, "active_key", None), "id", None),
        session_id=session.id,
        challenge_id=challenge.id,
        action=KeyUsageLog.Action.VERIFY,
        result=KeyUsageLog.Result.OK,
        metadata={"trust_decision": "verified", "actor_type": actor_type},
    )
    return session, decision_token

def _consume_challenge_and_count(
    session: VerificationSession,
    challenge: VerificationChallenge,
    failure_reason: str,
):

    challenge.mark_as_used(commit=True)
    session.attempt_count = (session.attempt_count or 0) + 1
    update_fields = ["attempt_count"]

    if session.attempts_exhausted:
        session.status = VerificationSession.Status.FAILED
        session.failure_reason = "attempts_exhausted"
        update_fields += ["status", "failure_reason"]

    session.save(update_fields=update_fields)

# ============================================================
# Decision token verification (used by org later)
# ============================================================

def verify_decision_token(
    *,
    organization,
    session_id,
    token: str,
) -> bool:
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
    if session.decision_token_hash is None:
        return False
    return secrets.compare_digest(
        session.decision_token_hash,
        sha256_hex(token),
    )

# ============================================================
# Cancellation
# ============================================================

@transaction.atomic
def cancel_session(session: VerificationSession, reason: str = "cancelled_by_org") -> bool:
    session = VerificationSession.objects.select_for_update().get(pk=session.pk)
    if session.is_final:
        return False
    session.status = VerificationSession.Status.CANCELLED
    session.failure_reason = reason
    session.save(update_fields=["status", "failure_reason"])
    return True
# API Key generation helper (for org_endpoints to use)

def generate_api_key_for_organization(organization) -> str:
    plaintext = "wq_" + secrets.token_urlsafe(40)
    organization.api_key_hash = hash_api_key(plaintext)
    organization.save(update_fields=["api_key_hash"])
    return plaintext