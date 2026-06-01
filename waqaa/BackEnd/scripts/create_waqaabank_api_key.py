"""
Create API key for waqaabank organization.

Run this ONCE in waqaa backend:
    python manage.py shell < scripts/create_waqaabank_api_key.py

The plaintext key prints ONCE — copy it to waqaabank's .env file as:
    WAQAA_ORG_API_KEY=<plaintext_key_here>

We use the same hash_api_key function the authentication layer uses,
so the key we create will be recognized by the auth class.
"""
import secrets

from core.utils_crypto import hash_api_key
from organization_endpoints.models import Organization, OrganizationApiKey


# ============================================================
# 1) Find waqaabank organization
# ============================================================
try:
    org = Organization.objects.get(name="waqaabank")
    print(f"✅ Organization found: {org.name}")
    print(f"   ID: {org.id}")
    print(f"   Status: {org.status}")
except Organization.DoesNotExist:
    print("❌ ERROR: Organization 'waqaabank' not found!")
    print("   Run: python manage.py create_test_organization 'waqaabank'")
    raise SystemExit(1)


# ============================================================
# 2) Generate a plaintext API key (32 random URL-safe bytes)
# ============================================================
plaintext_key = secrets.token_urlsafe(32)
key_hash = hash_api_key(plaintext_key)

print("\n" + "=" * 60)
print("⚠️  COPY THE PLAINTEXT KEY NOW (it will NEVER be shown again)")
print("=" * 60)
print(f"WAQAA_ORG_API_KEY={plaintext_key}")
print("=" * 60 + "\n")


# ============================================================
# 3) Create the OrganizationApiKey row
# ============================================================
api_key = OrganizationApiKey.objects.create(
    organization=org,
    key_hash=key_hash,
    label="waqaabank-demo-key",
    scopes=[
        OrganizationApiKey.SCOPE_SESSION_CREATE,
        OrganizationApiKey.SCOPE_SESSION_READ,
        OrganizationApiKey.SCOPE_SESSION_CANCEL,
        OrganizationApiKey.SCOPE_AUDIT_READ,
    ],
    is_active=True,
    rate_limit_per_minute=120,
)

print(f"✅ API Key created:")
print(f"   key_id (UUID): {api_key.id}")
print(f"   label: {api_key.label}")
print(f"   scopes: {api_key.scopes}")
print(f"   is_active: {api_key.is_active}")
print()
print("📝 Next steps:")
print("   1. Copy WAQAA_ORG_API_KEY line above into waqaabank's .env")
print("   2. Restart waqaabank server")
print("   3. Run script to link a client to waqaa account (next script)")