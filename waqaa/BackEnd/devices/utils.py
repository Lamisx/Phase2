import hmac
import hashlib
from django.conf import settings


def hash_national_id(national_id: str) -> str:
    """
    Convert national_id into HMAC-SHA256
    so the real ID is never stored in database.
    """

    return hmac.new(
        settings.SECRET_KEY.encode(),
        national_id.encode(),
        hashlib.sha256
    ).hexdigest()