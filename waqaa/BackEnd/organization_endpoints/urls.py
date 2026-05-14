"""Organization URL routes."""
from django.urls import path
 
from .views import (
    LinkUserView,
    OrganizationApiKeyListView,
    OrganizationSelfView,
    OrganizationUserListView,
)
 
 
app_name = "organization"
 
urlpatterns = [
    path("me/",          OrganizationSelfView.as_view(),     name="me"),
    path("api-keys/",    OrganizationApiKeyListView.as_view(), name="api-key-list"),
    path("links/",       LinkUserView.as_view(),             name="link-create"),
    path("links/list/",  OrganizationUserListView.as_view(), name="link-list"),
]