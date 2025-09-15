from django.urls import path
from . import views

urlpatterns = [
    # Ví dụ route test
    path("test/", views.test_view, name="test"),
]
