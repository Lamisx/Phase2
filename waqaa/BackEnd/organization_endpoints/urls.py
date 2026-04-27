from django.urls import path
from . import views

from django.urls import path, include

urlpatterns = [
     path("link-user/", views.link_user),
#    path("link-user/", views.link_user, name="link_user"),

]

