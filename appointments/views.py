# appointments/views.py

from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework_simplejwt.authentication import JWTAuthentication

from .models import Appointment
from .serializers import AppointmentSerializer

class AppointmentViewSet(viewsets.ModelViewSet):
    """
    ViewSet để quản lý Lịch hẹn (Appointment).
    - Bệnh nhân (Patient) có thể tạo, xem, và hủy lịch hẹn của mình.
    - Bác sĩ (Doctor) có thể xem, xác nhận, và hoàn thành lịch hẹn của mình.
    """
    serializer_class = AppointmentSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Tùy chỉnh queryset dựa trên vai trò người dùng:
        - Bệnh nhân chỉ thấy lịch của họ.
        - Bác sĩ chỉ thấy lịch của họ.
        - Admin/Staff thấy tất cả.
        """
        user = self.request.user
        
        if user.is_staff:
            return Appointment.objects.all().order_by('-date', '-time')
            
        if hasattr(user, 'patient'):
            # Nếu là bệnh nhân
            return Appointment.objects.filter(patient=user.patient).order_by('-date', '-time')
        elif hasattr(user, 'doctor'):
            # Nếu là bác sĩ
            return Appointment.objects.filter(doctor=user.doctor).order_by('-date', '-time')
        
        # Người dùng khác (không phải patient/doctor/staff) không thấy gì
        return Appointment.objects.none()

    def perform_create(self, serializer):
        """
        Tự động gán 'patient' là bệnh nhân đang đăng nhập khi tạo lịch hẹn.
        Trạng thái ban đầu luôn là 'pending'.
        """
        if not hasattr(self.request.user, 'patient'):
            raise PermissionDenied("Chỉ có bệnh nhân mới có thể đặt lịch hẹn.")
            
        patient = self.request.user.patient
        serializer.save(patient=patient, status="pending")

    # --- Custom Actions để thay đổi trạng thái ---

    @action(detail=True, methods=['patch'], url_path='cancel')
    def cancel_appointment(self, request, pk=None):
        """
        Action cho phép Bệnh nhân hủy lịch hẹn của chính họ.
        """
        appointment = self.get_object()
        user = request.user

        # Chỉ chủ nhân của lịch hẹn (bệnh nhân) mới được hủy
        if not hasattr(user, 'patient') or appointment.patient != user.patient:
            raise PermissionDenied("Bạn không có quyền hủy lịch hẹn này.")

        if appointment.status in ['completed', 'canceled']:
            raise ValidationError(f"Không thể hủy lịch hẹn đã {appointment.status}.")

        appointment.status = "canceled"
        appointment.save()
        serializer = self.get_serializer(appointment)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['patch'], url_path='confirm')
    def confirm_appointment(self, request, pk=None):
        """
        Action cho phép Bác sĩ xác nhận lịch hẹn.
        """
        appointment = self.get_object()
        user = request.user

        # Chỉ bác sĩ của lịch hẹn mới được xác nhận
        if not hasattr(user, 'doctor') or appointment.doctor != user.doctor:
            raise PermissionDenied("Bạn không có quyền xác nhận lịch hẹn này.")

        if appointment.status != 'pending':
            raise ValidationError(f"Chỉ có thể xác nhận lịch hẹn 'pending'.")

        appointment.status = "confirmed"
        appointment.save()
        serializer = self.get_serializer(appointment)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['patch'], url_path='complete')
    def complete_appointment(self, request, pk=None):
        """
        Action cho phép Bác sĩ đánh dấu lịch hẹn là đã hoàn thành.
        """
        appointment = self.get_object()
        user = request.user

        # Chỉ bác sĩ của lịch hẹn mới được hoàn thành
        if not hasattr(user, 'doctor') or appointment.doctor != user.doctor:
            raise PermissionDenied("Bạn không có quyền hoàn thành lịch hẹn này.")

        if appointment.status != 'confirmed':
            raise ValidationError(f"Chỉ có thể hoàn thành lịch hẹn đã 'confirmed'.")

        appointment.status = "completed"
        appointment.save()
        serializer = self.get_serializer(appointment)
        return Response(serializer.data, status=status.HTTP_200_OK)