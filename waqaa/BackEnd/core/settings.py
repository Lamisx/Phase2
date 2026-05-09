import os
from pathlib import Path
from dotenv import load_dotenv


# Build paths inside the project like this: BASE_DIR / 'subdir'.AC
BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / ".env")
# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/
# ============================================================
# Helper for required env vars
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
# Core Django
# ============================================================
DEBUG = env_bool("DJANGO_DEBUG", False)
# In production, SECRET_KEY MUST be set via env. In dev we tolerate a fallback.
SECRET_KEY = env(
    "DJANGO_SECRET_KEY",
    default=("unsafe-dev-key-do-not-use-in-prod" if DEBUG else None),
    required=not DEBUG,
)

ALLOWED_HOSTS = env_list("DJANGO_ALLOWED_HOSTS", "127.0.0.1,localhost")

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.postgres',
    'rest_framework',
    'accounts_endpoints',
    'devices_endpoints',
    'organization_endpoints',
    'verification_endpoint',
    'devices',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'organization_endpoints.middleware.api_key_middleware.APIKeyMiddleware',

]

ROOT_URLCONF = 'core.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'core.wsgi.application'


# Database
DATABASES = {

    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME":     env("DB_NAME", required=True),
        "USER":     env("DB_USER", required=True),
        "PASSWORD": env("DB_PASSWORD", required=True),
        "HOST":     env("DB_HOST", required=True),
        "PORT":     env("DB_PORT", default="5432"),
        "CONN_MAX_AGE": env_int("DB_CONN_MAX_AGE", 60),

    }
}

# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',},
]


# Internationalization
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
STATIC_URL = 'static/'
# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Cache (required for throttling)
REDIS_URL = env("REDIS_URL", default=None)
if REDIS_URL:
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.redis.RedisCache",
            "LOCATION": REDIS_URL,
        }
    }
else:
    # Local memory cache — fine for dev, NOT suitable for multi-process production
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "waqa-default-cache",
        }
    }

# Django REST Framework

REST_FRAMEWORK = {
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ],
    "DEFAULT_PARSER_CLASSES": [
        "rest_framework.parsers.JSONParser",
    ],
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.ScopedRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        # Per-organization throttles (used by OrgScopedThrottle)
        "verify_create": "60/min",     # session creation
        "verify_read":   "300/min",    # status / token verification / lists
        # Per-IP throttle for the public signature endpoint
        "verify_signature": "30/min",
    },
}
# Waqa — Verification Settings 
API_KEY_PEPPER = env("WAQA_API_KEY_PEPPER", required=not DEBUG)

# Verification session lifetime (minutes)
VERIFICATION_SESSION_TTL_MINUTES = env_int("WAQA_SESSION_TTL_MINUTES", 5)

# Challenge lifetime (seconds) — should be short
VERIFICATION_CHALLENGE_TTL_SECONDS = env_int("WAQA_CHALLENGE_TTL_SECONDS", 120)

# Production security hardening (only when DEBUG=False)
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 60 * 60 * 24 * 30  # 30 days
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_REFERRER_POLICY = "same-origin"
    X_FRAME_OPTIONS = "DENY"
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")