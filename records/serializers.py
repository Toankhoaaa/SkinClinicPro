from rest_framework import serializers

from .models import AppointmentRecord
from appointments.models import Appointment


class AppointmentRecordSerializer(serializers.ModelSerializer):
    appointment_id = serializers.PrimaryKeyRelatedField(
        queryset=Appointment.objects.all(),
        source='appointment',
        write_only=True
    )

    class Meta:
        model = AppointmentRecord
        fields = [
            'id',
            'appointment',
            'appointment_id',
            'reason',
            'description',
            'status_before',
            'status_after',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'appointment', 'created_at', 'updated_at']

