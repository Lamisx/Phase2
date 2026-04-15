from django.urls import path
from . import views

from django.urls import path, include

urlpatterns = [
     path("link-user/", views.link_user),

]
