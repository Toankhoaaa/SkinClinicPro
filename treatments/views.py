from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework_simplejwt.authentication import JWTAuthentication

from .models import Treatment
from .serializers import TreatmentSerializer
from appointments.models import Appointment


class TreatmentViewSet(viewsets.ModelViewSet):
    serializer_class = TreatmentSerializer
    queryset = Treatment.objects.select_related(
        'appointment',
        'appointment__doctor',
        'appointment__patient',
        'drug'
    ).all()
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return self.queryset.order_by('-id')
        if hasattr(user, 'doctor'):
            return self.queryset.filter(
                appointment__doctor=user.doctor
            ).order_by('-id')
        if hasattr(user, 'patient'):
            return self.queryset.filter(
                appointment__patient=user.patient
            ).order_by('-id')
        return self.queryset.none()

    def perform_create(self, serializer):
        user = self.request.user
        appointment: Appointment = serializer.validated_data['appointment']

        if hasattr(user, 'doctor') and appointment.doctor != user.doctor:
            raise PermissionDenied("Bạn không thể kê đơn cho lịch hẹn này.")

        if hasattr(user, 'patient'):
            raise PermissionDenied("Bệnh nhân không được tạo phác đồ điều trị.")

        if not (user.is_staff or hasattr(user, 'doctor')):
            raise PermissionDenied("Bạn không có quyền tạo phác đồ điều trị.")

        serializer.save()

    def perform_update(self, serializer):
        user = self.request.user
        treatment = self.get_object()

        if hasattr(user, 'doctor') and treatment.appointment.doctor != user.doctor:
            raise PermissionDenied("Bạn không thể chỉnh sửa phác đồ điều trị này.")

        if hasattr(user, 'patient'):
            raise PermissionDenied("Bệnh nhân không được chỉnh sửa phác đồ điều trị.")

        if not (user.is_staff or hasattr(user, 'doctor')):
            raise PermissionDenied("Bạn không có quyền chỉnh sửa phác đồ điều trị.")

        serializer.save()
