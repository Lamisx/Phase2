
from django.test import TestCase
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model

from organization_endpoints.models import (
    Organization,
    OrganizationApiKey,
    OrganizationUser
)

User = get_user_model()


class APISecurityTests(TestCase):

    def setUp(self):
        self.client = APIClient()

        # 👤 إنشاء مستخدم
        self.user = User.objects.create_user(
            username="testuser",
            password="123456"
        )

        # 🏢 إنشاء منظمة
        self.org = Organization.objects.create(
            name="Test Org",
            created_by=self.user
        )

        # 🔑 API Key
        self.api_key = OrganizationApiKey.objects.create(
            organization=self.org,
            key_hash="testkey123",
            scopes=["session:create"],
            rate_limit_per_minute=10
        )

        # 🔗 ربط المستخدم كـ admin
        OrganizationUser.objects.create(
            organization=self.org,
            user=self.user,
            role="admin",
            external_provider="internal",
            external_user_ref="123"
        )

        # endpoint (عدله حسب عندك)
        self.url = "/link-user/"


    # =========================
    # ✅ 1. API Key صحيح
    # =========================
    def test_valid_api_key(self):
        response = self.client.post(
            self.url,
            {},
            format='json',
            HTTP_X_API_KEY="testkey123"
        )

        self.assertNotEqual(response.status_code, 401)


    # =========================
    # ❌ 2. API Key خاطئ
    # =========================
    def test_invalid_api_key(self):
        response = self.client.post(
            self.url,
            {},
            format='json',
            HTTP_X_API_KEY="wrongkey"
        )

        self.assertEqual(response.status_code, 401)


    # =========================
    # ❌ 3. بدون API Key
    # =========================
    def test_missing_api_key(self):
        response = self.client.post(
            self.url,
            {},
            format='json'
        )

        self.assertEqual(response.status_code, 401)


    # =========================
    # ❌ 4. Scope غير مسموح
    # =========================
    def test_permission_denied(self):

        # نغير الصلاحيات
        self.api_key.scopes = ["audit:read"]
        self.api_key.save()

        response = self.client.post(
            self.url,
            {},
            format='json',
            HTTP_X_API_KEY="testkey123"
        )

        self.assertEqual(response.status_code, 403)


    # =========================
    # ❌ 5. Rate Limit
    # =========================
    def test_rate_limit(self):

        for _ in range(11):
            response = self.client.post(
                self.url,
                {},
                format='json',
                HTTP_X_API_KEY="testkey123"
            )

        self.assertEqual(response.status_code, 429)