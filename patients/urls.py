# patients/urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PatientViewSet

# 1. Tạo một router
router = DefaultRouter()

# 2. Đăng ký PatientViewSet với router
# 'patients' là tiền tố URL (ví dụ: /api/patients/)
router.register(r'patients', PatientViewSet, basename='patient')

# 3. Thêm các URL của router vào urlpatterns
urlpatterns = [
    path('', include(router.urls)),
]