from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import AppointmentRecordViewSet

router = DefaultRouter()
router.register(r'appointment-records', AppointmentRecordViewSet, basename='appointment-record')

urlpatterns = [
    path('', include(router.urls)),
]

