from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework_simplejwt.authentication import JWTAuthentication

from .models import AppointmentRecord
from .serializers import AppointmentRecordSerializer
from appointments.models import Appointment


class AppointmentRecordViewSet(viewsets.ModelViewSet):
    serializer_class = AppointmentRecordSerializer
    queryset = AppointmentRecord.objects.select_related(
        'appointment',
        'appointment__doctor',
        'appointment__patient'
    ).all()
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return self.queryset.order_by('-created_at')
        if hasattr(user, 'doctor'):
            return self.queryset.filter(
                appointment__doctor=user.doctor
            ).order_by('-created_at')
        if hasattr(user, 'patient'):
            return self.queryset.filter(
                appointment__patient=user.patient
            ).order_by('-created_at')
        return self.queryset.none()

    def perform_create(self, serializer):
        user = self.request.user
        appointment: Appointment = serializer.validated_data['appointment']

        if hasattr(user, 'patient') and appointment.patient != user.patient:
            raise PermissionDenied("Bạn không thể tạo hồ sơ khám cho lịch hẹn này.")

        if hasattr(user, 'doctor') and appointment.doctor != user.doctor:
            raise PermissionDenied("Bạn không thể tạo hồ sơ khám cho lịch hẹn này.")

        if not (user.is_staff or hasattr(user, 'doctor')):
            raise PermissionDenied("Chỉ có bác sĩ hoặc quản trị viên mới có thể tạo hồ sơ khám.")

        if AppointmentRecord.objects.filter(appointment=appointment).exists():
            raise ValidationError("Lịch hẹn đã có hồ sơ khám.")

        serializer.save()

    def perform_update(self, serializer):
        user = self.request.user
        record = self.get_object()

        if hasattr(user, 'doctor') and record.appointment.doctor != user.doctor:
            raise PermissionDenied("Bạn không thể chỉnh sửa hồ sơ khám này.")

        if hasattr(user, 'patient') and record.appointment.patient != user.patient:
            raise PermissionDenied("Bạn không thể chỉnh sửa hồ sơ khám này.")

        if not (user.is_staff or hasattr(user, 'doctor')):
            raise PermissionDenied("Chỉ bác sĩ hoặc quản trị viên mới có quyền chỉnh sửa.")

        serializer.save()
