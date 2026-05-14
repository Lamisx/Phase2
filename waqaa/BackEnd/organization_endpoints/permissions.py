"""
DRF permission classes for organization API key authentication.
 
These work together with OrganizationAPIKeyAuthentication. After successful
authentication, request.auth is an OrganizationApiKey instance.
"""
from rest_framework import permissions
 
from .models import OrganizationApiKey
 
 
class HasOrganizationAPIKey(permissions.BasePermission):
    """Request must be authenticated via OrganizationAPIKeyAuthentication."""
 
    message = "A valid organization API key is required."
 
    def has_permission(self, request, view):
        return isinstance(request.auth, OrganizationApiKey)
 
 
class HasScope(permissions.BasePermission):
    """Require a specific scope on the API key.
 
    The view declares:
        class MyView(APIView):
            required_scope = OrganizationApiKey.SCOPE_AUDIT_READ
    """
 
    message = "Required scope is missing from this API key."
 
    def has_permission(self, request, view):
        api_key = request.auth
        if not isinstance(api_key, OrganizationApiKey):
            return False
 
        required = getattr(view, "required_scope", None)
        if required is None:
            return True  # No specific scope required.
 
        return required in (api_key.scopes or [])