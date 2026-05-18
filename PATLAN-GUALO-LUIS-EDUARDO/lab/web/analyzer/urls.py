from django.urls import path

from . import views

urlpatterns = [
    path("", views.spa, name="index"),
]
