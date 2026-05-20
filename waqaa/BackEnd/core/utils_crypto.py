import base64
import hashlib
import hmac
import secrets

from typing import Optional, Union

from cryptography.exceptions import InvalidSignature

from cryptography.fernet import (
    Fernet,
    InvalidToken,
)

from cryptography.hazmat.primitives import hashes

from cryptography.hazmat.primitives.asymmetric import ec

from cryptography.hazmat.primitives.serialization import (
    load_der_public_key,
)

from django.conf import settings


# ============================================================
# Internal Helpers
# ============================================================

def _require_setting(name: str) -> str:

    value = getattr(settings, name, None)

    if value is None or value == "":

        raise RuntimeError(
            f"Required setting '{name}' is not configured"
        )

    return value


def _to_bytes(value: Union[str, bytes]) -> bytes:

    return (
        value.encode("utf-8")
        if isinstance(value, str)
        else value
    )


# ============================================================
# HMAC Hashing
# ============================================================

def _hmac_sha256_hex(
    key: str,
    message: str,
) -> str:

    return hmac.new(
        key.encode("utf-8"),
        message.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def hash_api_key(api_key: str) -> str:

    pepper = _require_setting(
        "API_KEY_PEPPER"
    )

    return _hmac_sha256_hex(
        pepper,
        api_key,
    )


# ============================================================
# National ID Hashing
# ============================================================

def hash_national_id_layer1(
    national_id: str,
) -> str:

    return hashlib.sha256(
        _to_bytes(national_id)
    ).hexdigest()


def hash_national_id_storage(
    shared_hash_hex: str,
) -> str:

    pepper = _require_setting(
        "NATIONAL_ID_PEPPER"
    )

    return _hmac_sha256_hex(
        pepper,
        shared_hash_hex,
    )


def hash_national_id(
    national_id: str,
) -> str:

    return hash_national_id_storage(
        hash_national_id_layer1(
            national_id
        )
    )


# ============================================================
# Plain Digests & Constant-Time Compare
# ============================================================

def sha256_hex(
    data: Union[str, bytes]
) -> str:

    return hashlib.sha256(
        _to_bytes(data)
    ).hexdigest()


def constant_time_equals(
    a: str,
    b: str,
) -> bool:

    return secrets.compare_digest(
        a or "",
        b or "",
    )


# ============================================================
# Random Tokens & API Keys
# ============================================================

def generate_token(
    num_bytes: int = 32
) -> str:

    return secrets.token_urlsafe(
        num_bytes
    )


def generate_random_bytes(
    num_bytes: int = 32
) -> bytes:

    return secrets.token_bytes(
        num_bytes
    )


def generate_api_key(
    prefix: str = "ak_"
) -> str:

    return (
        f"{prefix}"
        f"{secrets.token_urlsafe(40)}"
    )


# ============================================================
# Symmetric Encryption (Fernet)
# ============================================================

def _get_fernet() -> Fernet:

    key = _require_setting(
        "PAYLOAD_ENCRYPTION_KEY"
    )

    if isinstance(key, str):

        key = key.encode("utf-8")

    return Fernet(key)


def encrypt_text(
    plaintext: Optional[str]
) -> Optional[str]:

    if plaintext is None:
        return None

    return (
        _get_fernet()
        .encrypt(
            plaintext.encode("utf-8")
        )
        .decode("utf-8")
    )


def decrypt_text(
    ciphertext: Optional[str]
) -> Optional[str]:

    if not ciphertext:
        return None

    try:

        return (
            _get_fernet()
            .decrypt(
                ciphertext.encode("utf-8")
            )
            .decode("utf-8")
        )

    except InvalidToken:

        return None


# ============================================================
# ES256 Signature Verification
# ============================================================

class SignatureMalformedError(Exception):
    """
    Input was not parseable
    as a valid signature/key.
    """


def _b64decode_strict(
    value: str
) -> bytes:

    try:

        return base64.b64decode(
            value,
            validate=True,
        )

    except Exception as exc:

        raise SignatureMalformedError(
            f"invalid_base64: {exc}"
        ) from exc


def load_es256_public_key_b64(
    public_key_b64: str,
):

    try:

        der_bytes = _b64decode_strict(
            public_key_b64
        )

        public_key = load_der_public_key(
            der_bytes
        )

        if not isinstance(
            public_key,
            ec.EllipticCurvePublicKey,
        ):

            raise SignatureMalformedError(
                "invalid_es256_public_key"
            )

        return public_key

    except Exception as exc:

        raise SignatureMalformedError(
            f"invalid_es256_public_key: {exc}"
        ) from exc


def verify_es256_signature(
    public_key_b64: str,
    message: Union[str, bytes],
    signature_b64: str,
) -> bool:

    public_key = load_es256_public_key_b64(
        public_key_b64
    )

    signature = _b64decode_strict(
        signature_b64
    )

    message_bytes = _to_bytes(
        message
    )

    try:

        public_key.verify(
            signature,
            message_bytes,
            ec.ECDSA(
                hashes.SHA256()
            ),
        )

        return True

    except InvalidSignature:

        return False