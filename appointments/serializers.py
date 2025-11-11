from rest_framework import serializers
from django.utils import timezone
from datetime import datetime

from .models import Appointment
from doctor.models import Doctor
from availability.models import Schedule
from patients.models import Patient
from accounts.models import User
from specialities.models import Speciality 
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'first_name', 'last_name', 'email', 'phone']

class SpecialitySerializer(serializers.ModelSerializer):
    """Serializer đơn giản cho Chuyên khoa."""
    class Meta:
        model = Speciality
        fields = ['id', 'name']

class SimpleDoctorSerializer(serializers.ModelSerializer):
    """Serializer đơn giản cho Doctor để hiển thị trong Appointment."""
    user = UserSerializer(read_only=True)
    specialty = SpecialitySerializer(read_only=True)
    
    class Meta:
        model = Doctor
        fields = ['id', 'user', 'specialty', 'price', 'experience']

class SimplePatientSerializer(serializers.ModelSerializer):
    """Serializer đơn giản cho Patient để hiển thị trong Appointment."""
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = Patient
        fields = ['id', 'user', 'health_insurance_number']

class AppointmentSerializer(serializers.ModelSerializer):
    patient = SimplePatientSerializer(read_only=True)
    doctor = SimpleDoctorSerializer(read_only=True)
    
    doctor_id = serializers.PrimaryKeyRelatedField(
        queryset=Doctor.objects.filter(is_available=True, verificationStatus="VERIFIED"),
        source='doctor',
        write_only=True,
        label="Doctor"
    )
    class Meta:
        model = Appointment
        fields = [
            'id', 'patient', 'doctor', 'doctor_id', 'date', 'time',
            'status', 'notes', 'created_at'
        ]
        read_only_fields = ('patient', 'status', 'created_at', 'updated_at')

    def validate(self, data):
        """
        Validation logic chính:
        1. Không đặt lịch trong quá khứ.
        2. Bác sĩ phải có lịch làm việc (Schedule) vào ngày đó.
        3. Giờ đặt phải nằm trong giờ làm việc của bác sĩ.
        4. Giờ đó chưa có ai đặt (hoặc chưa được xác nhận).
        5. Lịch của bác sĩ không vượt quá số lượng bệnh nhân tối đa.
        """
        date = data['date']
        time = data['time']
        doctor = data['doctor']

        try:
            appointment_datetime = timezone.make_aware(datetime.combine(date, time))
        except Exception:
            appointment_datetime = datetime.combine(date, time)
            if timezone.is_aware(appointment_datetime):
                pass
            else:
                appointment_datetime = timezone.make_aware(appointment_datetime)

        if appointment_datetime < timezone.now():
            raise serializers.ValidationError("Không thể đặt lịch hẹn trong quá khứ.")

        try:
            schedule = Schedule.objects.get(
                doctor=doctor, 
                date=date, 
                is_available=True
            )
        except Schedule.DoesNotExist:
            raise serializers.ValidationError(f"Bác sĩ không có lịch làm việc vào ngày {date}.")

        if not (schedule.start_time <= time <= schedule.end_time):
            raise serializers.ValidationError(
                f"Giờ hẹn phải nằm trong khoảng làm việc của bác sĩ ({schedule.start_time} - {schedule.end_time})."
            )

        existing_appointment = Appointment.objects.filter(
            doctor=doctor,
            date=date,
            time=time,
            status__in=["pending", "confirmed"]
        ).exists()

        if existing_appointment:
            raise serializers.ValidationError("Khung giờ này đã có người đặt. Vui lòng chọn giờ khác.")

        day_appointment_count = Appointment.objects.filter(
            doctor=doctor,
            date=date,
            status__in=["pending", "confirmed"]
        ).count()

        if schedule.max_patients is not None and day_appointment_count >= schedule.max_patients:
            raise serializers.ValidationError("Bác sĩ đã đạt số lượng bệnh nhân tối đa trong ngày này.")

        return data