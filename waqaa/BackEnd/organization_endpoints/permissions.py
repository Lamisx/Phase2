
from rest_framework.response import Response
from rest_framework import status
from functools import wraps


def require_scope(required_scope):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            api_key = getattr(request, "api_key", None)

            # ❌ لا يوجد API Key
            if not api_key:
                return Response(
                    {"error": "API key missing"},
                    status=status.HTTP_401_UNAUTHORIZED
                )

            # ❌ لا يملك الصلاحية
            if required_scope not in api_key.scopes:
                return Response(
                    {"error": "Permission denied"},
                    status=status.HTTP_403_FORBIDDEN
                )

            return view_func(request, *args, **kwargs)

        return wrapper
    return decorator