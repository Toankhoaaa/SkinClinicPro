from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError # <--- Quan trọng
from rest_framework.decorators import action
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.utils.dateparse import parse_date
from datetime import datetime, timedelta

from .models import Schedule
from .serializers import ScheduleSerializer
from doctor.models import Doctor

class ScheduleViewSet(viewsets.ModelViewSet):
    serializer_class = ScheduleSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Schedule.objects.all().order_by('date')
        if hasattr(user, 'doctor'):
            return Schedule.objects.filter(doctor=user.doctor).order_by('date')
        return Schedule.objects.none()

    def perform_create(self, serializer):
        user = self.request.user
        if not hasattr(user, 'doctor'):
            raise PermissionDenied("Chỉ có bác sĩ mới được tạo lịch làm việc.")
        
        try:
            serializer.save(doctor=user.doctor)
        except IntegrityError:
            # Bắt lỗi trùng lịch từ DB và trả về lỗi đẹp
            raise ValidationError({"detail": "Lịch làm việc cho ngày này đã tồn tại."})
        
    @action(detail=False, methods=['post'], url_path='copy-week')
    def copy_week(self, request):
        """
        Sao chép lịch làm việc trong 1 tuần sang tuần mới.
        Body:
            - source_start: ngày bắt đầu tuần nguồn (YYYY-MM-DD)
            - target_start: ngày bắt đầu tuần đích (YYYY-MM-DD)
            - doctor_id: (tùy chọn) dùng khi admin sao chép cho bác sĩ khác
        """
        source_start_str = request.data.get('source_start')
        target_start_str = request.data.get('target_start')
        doctor_id = request.data.get('doctor_id')

        user = request.user
        if hasattr(user, 'doctor'):
            doctor = user.doctor
        elif user.is_staff:
            if not doctor_id:
                return Response(
                    {"detail": "doctor_id là bắt buộc khi admin thực hiện thao tác này."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            try:
                doctor = Doctor.objects.get(id=doctor_id)
            except Doctor.DoesNotExist:
                return Response(
                    {"detail": "Không tìm thấy bác sĩ."},
                    status=status.HTTP_404_NOT_FOUND
                )
        else:
            raise PermissionDenied("Bạn không được phép sao chép lịch làm việc.")

        source_start = parse_date(source_start_str) if source_start_str else None
        target_start = parse_date(target_start_str) if target_start_str else None

        if not source_start or not target_start:
            return Response(
                {"detail": "source_start và target_start là bắt buộc và phải đúng định dạng YYYY-MM-DD."},
                status=status.HTTP_400_BAD_REQUEST
            )

        created_count = 0
        updated_count = 0
        skipped_dates = []

        for day_offset in range(7):
            source_date = source_start + timedelta(days=day_offset)
            target_date = target_start + timedelta(days=day_offset)

            try:
                template_schedule = Schedule.objects.get(doctor=doctor, date=source_date)
            except Schedule.DoesNotExist:
                skipped_dates.append(source_date.isoformat())
                continue

            defaults = {
                'start_time': template_schedule.start_time,
                'end_time': template_schedule.end_time,
                'is_available': template_schedule.is_available,
                'max_patients': template_schedule.max_patients,
            }

            _, created = Schedule.objects.update_or_create(
                doctor=doctor,
                date=target_date,
                defaults=defaults
            )
            if created:
                created_count += 1
            else:
                updated_count += 1

        return Response(
            {
                "doctor_id": doctor.id,
                "source_start": source_start.isoformat(),
                "target_start": target_start.isoformat(),
                "created": created_count,
                "updated": updated_count,
                "skipped_without_source": skipped_dates,
            },
            status=status.HTTP_200_OK
        )