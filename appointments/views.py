# appointments/views.py

from rest_framework import viewsets, status
from datetime import datetime, timedelta

from django.utils import timezone
from django.utils.dateparse import parse_date
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework_simplejwt.authentication import JWTAuthentication

from .models import Appointment
from .serializers import AppointmentSerializer
from availability.models import Schedule
from doctor.models import Doctor
from records.models import AppointmentRecord
from notifications.models import Notification

CANCEL_CUTOFF_HOURS = 12
RESCHEDULE_CUTOFF_HOURS = 12


def get_aware_datetime(date_value, time_value):
    combined = datetime.combine(date_value, time_value)
    current_tz = timezone.get_current_timezone()
    if timezone.is_naive(combined):
        return timezone.make_aware(combined, current_tz)
    return combined.astimezone(current_tz)

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

    def _notify(self, users, message, notif_type):
        notifications = [
            Notification(user=user, message=message, type=notif_type)
            for user in users if user is not None
        ]
        if notifications:
            Notification.objects.bulk_create(notifications)

    @staticmethod
    def _format_slot(appointment):
        return f"{appointment.date.isoformat()} {appointment.time.strftime('%H:%M')}"

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
        appointment = serializer.instance
        doctor_user = appointment.doctor.user if appointment.doctor else None
        patient_name = patient.user.get_full_name() or patient.user.username
        self._notify(
            [doctor_user],
            f"Bệnh nhân {patient_name} đã đặt lịch hẹn mới vào {self._format_slot(appointment)}.",
            "appointment_created"
        )

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

        appointment_datetime = get_aware_datetime(appointment.date, appointment.time)
        if appointment_datetime - timezone.now() < timedelta(hours=CANCEL_CUTOFF_HOURS):
            raise ValidationError(
                f"Không thể hủy lịch hẹn trong vòng {CANCEL_CUTOFF_HOURS} giờ trước giờ khám."
            )

        appointment.status = "canceled"
        appointment.save()
        serializer = self.get_serializer(appointment)
        doctor_user = appointment.doctor.user if appointment.doctor else None
        patient_name = appointment.patient.user.get_full_name() or appointment.patient.user.username
        self._notify(
            [doctor_user],
            f"Bệnh nhân {patient_name} đã hủy lịch hẹn vào {self._format_slot(appointment)}.",
            "appointment_canceled"
        )
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
        patient_user = appointment.patient.user if appointment.patient else None
        doctor_name = appointment.doctor.user.get_full_name() or appointment.doctor.user.username
        self._notify(
            [patient_user],
            f"Lịch hẹn với bác sĩ {doctor_name} vào {self._format_slot(appointment)} đã được xác nhận.",
            "appointment_confirmed"
        )
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

        record, _ = AppointmentRecord.objects.get_or_create(appointment=appointment)
        updated = False
        for field in ['reason', 'description', 'status_before', 'status_after']:
            value = request.data.get(field)
            if value is not None:
                setattr(record, field, value)
                updated = True
        if updated:
            record.save()

        serializer = self.get_serializer(appointment)
        patient_user = appointment.patient.user if appointment.patient else None
        doctor_name = appointment.doctor.user.get_full_name() or appointment.doctor.user.username
        self._notify(
            [patient_user],
            f"Buổi khám với bác sĩ {doctor_name} vào {self._format_slot(appointment)} đã hoàn thành. Vui lòng xem hồ sơ khám.",
            "appointment_completed"
        )
        return Response(
            {
                "appointment": serializer.data,
                "record_id": record.id,
            },
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=['patch'], url_path='reschedule')
    def reschedule_appointment(self, request, pk=None):
        """
        Action cho phép Bệnh nhân đổi lịch hẹn sang ngày/giờ khác.
        """
        appointment = self.get_object()
        user = request.user

        if appointment.status in ['completed', 'canceled']:
            raise ValidationError("Không thể đổi lịch đã hoàn thành hoặc đã hủy.")

        if not hasattr(user, 'patient') and not user.is_staff:
            raise PermissionDenied("Chỉ bệnh nhân hoặc quản trị viên mới có thể đổi lịch hẹn.")

        if hasattr(user, 'patient') and appointment.patient != user.patient and not user.is_staff:
            raise PermissionDenied("Bạn không có quyền đổi lịch hẹn này.")

        appointment_datetime = get_aware_datetime(appointment.date, appointment.time)
        if appointment_datetime - timezone.now() < timedelta(hours=RESCHEDULE_CUTOFF_HOURS):
            raise ValidationError(
                f"Không thể đổi lịch hẹn trong vòng {RESCHEDULE_CUTOFF_HOURS} giờ trước giờ khám."
            )

        new_date = request.data.get('date')
        new_time = request.data.get('time')
        if not new_date or not new_time:
            raise ValidationError("Cần cung cấp đầy đủ trường 'date' và 'time' khi đổi lịch.")

        try:
            parsed_time = datetime.strptime(new_time, "%H:%M").time()
        except ValueError:
            raise ValidationError("Định dạng giờ không hợp lệ. Giờ phải theo định dạng HH:MM.")

        parsed_date = parse_date(new_date)
        if parsed_date is None:
            raise ValidationError("Định dạng ngày không hợp lệ. Định dạng đúng: YYYY-MM-DD.")

        serializer = AppointmentSerializer(
            appointment,
            data={
                'date': parsed_date,
                'time': parsed_time,
                'doctor_id': appointment.doctor.id,
            },
            partial=True,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save(status="pending")
        appointment.refresh_from_db(fields=['date', 'time', 'status'])

        doctor_user = appointment.doctor.user if appointment.doctor else None
        patient_user = appointment.patient.user if appointment.patient else None
        slot_label = self._format_slot(appointment)

        self._notify(
            [doctor_user],
            f"Bệnh nhân đã đổi lịch hẹn sang {slot_label}.",
            "appointment_rescheduled"
        )
        self._notify(
            [patient_user],
            f"Lịch hẹn của bạn đã được đổi sang {slot_label} và đang chờ xác nhận.",
            "appointment_rescheduled"
        )

        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], url_path='available-slots', permission_classes=[AllowAny])
    def available_slots(self, request):
        """
        Trả về danh sách slot trống theo bác sĩ và ngày.
        Query params:
            - doctor_id (bắt buộc)
            - date (YYYY-MM-DD, bắt buộc)
            - slot_duration (phút, mặc định 30)
        """
        doctor_id = request.query_params.get('doctor_id')
        date_str = request.query_params.get('date')
        slot_duration = request.query_params.get('slot_duration', 30)

        if not doctor_id or not date_str:
            return Response(
                {"detail": "doctor_id và date là bắt buộc."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            doctor = Doctor.objects.get(id=doctor_id, is_available=True, verificationStatus="VERIFIED")
        except Doctor.DoesNotExist:
            return Response(
                {"detail": "Không tìm thấy bác sĩ hợp lệ."},
                status=status.HTTP_404_NOT_FOUND
            )

        try:
            slot_duration = int(slot_duration)
            if slot_duration <= 0:
                raise ValueError
        except ValueError:
            return Response(
                {"detail": "slot_duration phải là số nguyên dương."},
                status=status.HTTP_400_BAD_REQUEST
            )

        appointment_date = parse_date(date_str)
        if appointment_date is None:
            return Response(
                {"detail": "Ngày không hợp lệ. Định dạng đúng: YYYY-MM-DD."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            schedule = Schedule.objects.get(
                doctor=doctor,
                date=appointment_date,
                is_available=True
            )
        except Schedule.DoesNotExist:
            return Response(
                {"detail": "Bác sĩ không có lịch làm việc trong ngày đã chọn."},
                status=status.HTTP_404_NOT_FOUND
            )

        if schedule.max_patients is not None:
            booked_count = Appointment.objects.filter(
                doctor=doctor,
                date=appointment_date,
                status__in=["pending", "confirmed"]
            ).count()
            if booked_count >= schedule.max_patients:
                return Response(
                    {
                        "doctor_id": doctor.id,
                        "date": appointment_date,
                        "slots": [],
                        "message": "Bác sĩ đã đạt số lượng bệnh nhân tối đa trong ngày."
                    },
                    status=status.HTTP_200_OK
                )

        existing_times = set(
            Appointment.objects.filter(
                doctor=doctor,
                date=appointment_date,
                status__in=["pending", "confirmed"]
            ).values_list('time', flat=True)
        )

        tz = timezone.get_current_timezone()
        start_dt = timezone.make_aware(datetime.combine(appointment_date, schedule.start_time), tz)
        end_dt = timezone.make_aware(datetime.combine(appointment_date, schedule.end_time), tz)
        now = timezone.now()
        delta = timedelta(minutes=slot_duration)

        slots = []
        current = start_dt
        while current + delta <= end_dt:
            if current >= now:
                slot_time = current.time()
                if slot_time not in existing_times:
                    slots.append(current.strftime("%H:%M"))
            current += delta

        return Response(
            {
                "doctor_id": doctor.id,
                "date": appointment_date.isoformat(),
                "slot_duration_minutes": slot_duration,
                "slots": slots,
            },
            status=status.HTTP_200_OK
        )