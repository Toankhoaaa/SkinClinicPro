from django.urls import path
from . import views

urlpatterns = [
    path("my_profile/", views.myProfileView, name="my_profile"),
    path("update_profile/", views.updateProfileView, name="update_profile"),
    path("delete_profile/", views.deleteProfileView, name="delete_profile"),
]