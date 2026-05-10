"""
Django settings for the Trust Verification project.

Reads configuration from environment variables (with safe development defaults).
"""
import os
import warnings
from datetime import timedelta
from pathlib import Path

from dotenv import load_dotenv


# ============================================================
# Paths & .env
# ============================================================
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


# ============================================================
# Environment helpers
# ============================================================
def env(key: str, default=None, required: bool = False):
    """Read an env var; raise if required and missing."""
    value = os.getenv(key, default)
    if required and (value is None or value == ""):
        raise RuntimeError(
            f"Required environment variable '{key}' is not set. "
            f"Add it to your .env file."
        )
    return value


def env_bool(key: str, default: bool = False) -> bool:
    return os.getenv(key, str(default)).strip().lower() in {"1", "true", "yes", "on"}


def env_int(key: str, default: int) -> int:
    try:
        return int(os.getenv(key, str(default)))
    except (TypeError, ValueError):
        return default


def env_list(key: str, default: str = "") -> list:
    raw = os.getenv(key, default)
    return [item.strip() for item in raw.split(",") if item.strip()]


# ============================================================
# Core
# ============================================================
DEBUG = env_bool("DJANGO_DEBUG", default=False)

SECRET_KEY = env(
    "DJANGO_SECRET_KEY",
    default="unsafe-dev-key-do-not-use-in-prod" if DEBUG else None,
    required=not DEBUG,
)

ALLOWED_HOSTS = env_list("DJANGO_ALLOWED_HOSTS", default="127.0.0.1,localhost")

ROOT_URLCONF = "core.urls"
WSGI_APPLICATION = "core.wsgi.application"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# AUTH_USER_MODEL uses the app *label* (not folder name).
# accounts_endpoints/apps.py sets label="account", which is why this works.
AUTH_USER_MODEL = "account.AccountUser"


# ============================================================
# Apps
# ============================================================
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.postgres",

    "rest_framework",
    "rest_framework_simplejwt",

    # Local apps — actual folder names on disk.
    "accounts_endpoints",       # internal label = "account" (set in apps.py)
    "organization_endpoints",
    "devices_endpoints",
    "verification_endpoint",
]


# ============================================================
# Middleware
# ============================================================
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]


# ============================================================
# Templates
# ============================================================
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]


# ============================================================
# Database
# ============================================================
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": env("DB_NAME", default="postgres", required=not DEBUG),
        "USER": env("DB_USER", default="postgres", required=not DEBUG),
        "PASSWORD": env("DB_PASSWORD", default="", required=not DEBUG),
        "HOST": env("DB_HOST", default="127.0.0.1"),
        "PORT": env("DB_PORT", default="5432"),
        "CONN_MAX_AGE": env_int("DB_CONN_MAX_AGE", default=60),
        "CONN_HEALTH_CHECKS": True,
    }
}


# ============================================================
# Password validation
# ============================================================
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {"min_length": 8},
    },
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]


# ============================================================
# Internationalization
# ============================================================
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True


# ============================================================
# Static files
# ============================================================
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"


# ============================================================
# Cache
# ============================================================
REDIS_URL = env("REDIS_URL", default=None)

if REDIS_URL:
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.redis.RedisCache",
            "LOCATION": REDIS_URL,
        }
    }
else:
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "default-cache",
        }
    }


# ============================================================
# Django REST Framework
# ============================================================
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
    "DEFAULT_RENDERER_CLASSES": (
        "rest_framework.renderers.JSONRenderer",
    ),
    "DEFAULT_PARSER_CLASSES": (
        "rest_framework.parsers.JSONParser",
    ),
    "DEFAULT_THROTTLE_CLASSES": (
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ),
    "DEFAULT_THROTTLE_RATES": {
        "anon": "60/min",
        "user": "300/min",
        "auth_login": "10/min",
        "auth_register": "10/min",
    },
}


# ============================================================
# Simple JWT
# ============================================================
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=env_int("JWT_ACCESS_MINUTES", default=30)),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=env_int("JWT_REFRESH_DAYS", default=7)),
    "ALGORITHM": "HS256",
    "SIGNING_KEY": SECRET_KEY,
    "AUTH_HEADER_TYPES": ("Bearer",),
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
}


# ============================================================
# Cryptography
# ============================================================
API_KEY_PEPPER = env(
    "API_KEY_PEPPER",
    default="dev-api-key-pepper" if DEBUG else None,
    required=not DEBUG,
)

NATIONAL_ID_PEPPER = env(
    "NATIONAL_ID_PEPPER",
    default="dev-national-id-pepper" if DEBUG else None,
    required=not DEBUG,
)

PAYLOAD_ENCRYPTION_KEY = env(
    "PAYLOAD_ENCRYPTION_KEY",
    default=None,
    required=not DEBUG,
)

if DEBUG and not PAYLOAD_ENCRYPTION_KEY:
    from cryptography.fernet import Fernet
    PAYLOAD_ENCRYPTION_KEY = Fernet.generate_key().decode("utf-8")
    warnings.warn(
        "PAYLOAD_ENCRYPTION_KEY not set — generated ephemeral key for development. "
        "Encrypted data will be unreadable after server restart.",
        RuntimeWarning,
        stacklevel=2,
    )


# ============================================================
# Reverse proxy
# ============================================================
TRUST_FORWARDED_HEADERS = env_bool("TRUST_FORWARDED_HEADERS", default=False)


# ============================================================
# Production hardening
# ============================================================
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 60 * 60 * 24 * 365
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_REFERRER_POLICY = "no-referrer"
    X_FRAME_OPTIONS = "DENY"

    if TRUST_FORWARDED_HEADERS:
        SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")