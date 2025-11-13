from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import SpecialityViewSet

router = DefaultRouter()
router.register(r'specialities', SpecialityViewSet, basename='speciality')

urlpatterns = [
    path('', include(router.urls)),
]

