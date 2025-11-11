# doctor/urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DoctorViewSet

# 1. Tạo một router
router = DefaultRouter()

# 2. Đăng ký DoctorViewSet với router
# 'doctors' là tiền tố URL (ví dụ: /api/doctors/)
router.register(r'doctors', DoctorViewSet, basename='doctor')

# 3. Thêm các URL của router vào urlpatterns
urlpatterns = [
    path('', include(router.urls)),
]