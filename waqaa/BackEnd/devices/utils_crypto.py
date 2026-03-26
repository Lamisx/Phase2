import base64
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey


def verify_ed25519_signature(public_key_b64: str, message: str, signature_b64: str) -> bool:
    """
    Verify Ed25519 signature.

    public_key_b64: base64 encoded public key
    message: original challenge string
    signature_b64: base64 encoded signature
    """

    try:
        public_key_bytes = base64.b64decode(public_key_b64)
        signature_bytes = base64.b64decode(signature_b64)
        message_bytes = message.encode()

        public_key = Ed25519PublicKey.from_public_bytes(public_key_bytes)
        public_key.verify(signature_bytes, message_bytes)

        return True
    except Exception:
        return False