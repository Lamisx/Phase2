from django.utils import timezone
from django.http import JsonResponse
from django.core.cache import cache

# from .models import OrganizationApiKey 
from organization_endpoints.models import OrganizationApiKey


class APIKeyMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):

        # 🔑 استخراج API Key من header
        api_key = request.headers.get("X-API-KEY")

        if not api_key:
            return JsonResponse({"error": "API key required"}, status=401)

        try:
            key = OrganizationApiKey.objects.get(key_hash=api_key)
        except OrganizationApiKey.DoesNotExist:
            return JsonResponse({"error": "Invalid API key"}, status=401)

        # ❌ inactive
        if not key.is_active:
            return JsonResponse({"error": "API key inactive"}, status=403)

        # ❌ revoked
        if key.revoked_at:
            return JsonResponse({"error": "API key revoked"}, status=403)

        # ❌ expired
        if key.expires_at and key.expires_at < timezone.now():
            return JsonResponse({"error": "API key expired"}, status=403)

        # ================================
        # 🔥 Rate Limiting (الإضافة هنا)
        # ================================

        cache_key = f"rate_limit:{key.id}"
        request_count = cache.get(cache_key, 0)

        if request_count >= key.rate_limit_per_minute:
            return JsonResponse(
                {"error": "Rate limit exceeded"},
                status=429
            )

        cache.set(cache_key, request_count + 1, timeout=60)

        # ================================

        # 📊 تحديث الاستخدام
        key.last_used_at = timezone.now()
        key.total_requests += 1
        key.save(update_fields=["last_used_at", "total_requests"])

        # 📌 ربط المفتاح بالطلب
        request.api_key = key

        return self.get_response(request)