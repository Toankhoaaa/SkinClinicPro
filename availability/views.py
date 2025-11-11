# availability/views.py
from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from rest_framework_simplejwt.authentication import JWTAuthentication

from .models import Schedule
from .serializers import ScheduleSerializer

class ScheduleViewSet(viewsets.ModelViewSet):
    """
    ViewSet cho phép Bác sĩ quản lý lịch làm việc (Schedule) của họ.
    - Bác sĩ chỉ thấy và quản lý lịch của mình.
    - Admin thấy và quản lý mọi lịch.
    """
    serializer_class = ScheduleSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Tùy chỉnh queryset: Bác sĩ chỉ thấy lịch của mình.
        """
        user = self.request.user
        
        if user.is_staff: # Admin
            return Schedule.objects.all().order_by('date')
        
        if hasattr(user, 'doctor'): # Bác sĩ
            return Schedule.objects.filter(doctor=user.doctor).order_by('date')
            
        # Bệnh nhân hoặc người khác không có lịch
        return Schedule.objects.none()

    def perform_create(self, serializer):
        """
        Tự động gán bác sĩ là người đang đăng nhập khi tạo lịch.
        """
        user = self.request.user
        if not hasattr(user, 'doctor'):
            raise PermissionDenied("Chỉ có bác sĩ mới được tạo lịch làm việc.")
        
        # Tự động gán doctor
        serializer.save(doctor=user.doctor)