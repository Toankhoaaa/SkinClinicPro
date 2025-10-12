from django.urls import path
from . import views

urlpatterns = [
    path("my_profile/", views.test_view, name="my_profile"),
]