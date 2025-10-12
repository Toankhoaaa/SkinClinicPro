from django.urls import path
from . import views

urlpatterns = [
    path("signup/", views.signUpView, name="signup"),
    path("login/", views.loginView, name="login"),
    path("logout/", views.logoutView, name="logout"),
    path("refresh/", views.RefreshTokenView.as_view(), name="refresh_token"),
]
