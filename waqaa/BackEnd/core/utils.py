
from typing import Optional

from django.conf import settings
from .utils_crypto import (  # noqa: E402, F401
    hash_api_key,
    hash_national_id,
)
# ============================================================
# Request helpers
# ============================================================
def get_client_ip(request) -> Optional[str]:

    if getattr(settings, "TRUST_FORWARDED_HEADERS", False):
        forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if forwarded_for:
            # The leftmost IP is the original client; the rest are proxies.
            return forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")

def get_user_agent(request, max_length: int = 512) -> Optional[str]:
    """Return the User-Agent header, truncated to max_length. None if empty."""
    user_agent = request.META.get("HTTP_USER_AGENT", "") or ""
    user_agent = user_agent[:max_length]
    return user_agent or None

# ============================================================
# String helpers
# ============================================================
def normalize_str(value: Optional[str]) -> Optional[str]:
    """Strip whitespace; return None for empty/None input."""
    if value is None:
        return None
    value = value.strip()
    return value or None


def normalize_lower(value: Optional[str]) -> Optional[str]:
    """Strip and lowercase; return None for empty/None input."""
    value = normalize_str(value)
    return value.lower() if value else None
