from rest_framework import serializers

from .models import Treatment
from appointments.models import Appointment
from drugs.models import Drug


class TreatmentSerializer(serializers.ModelSerializer):
    appointment_id = serializers.PrimaryKeyRelatedField(
        queryset=Appointment.objects.all(),
        source='appointment',
        write_only=True
    )
    drug_id = serializers.PrimaryKeyRelatedField(
        queryset=Drug.objects.all(),
        source='drug',
        required=False,
        allow_null=True,
        write_only=True
    )

    class Meta:
        model = Treatment
        fields = [
            'id',
            'appointment',
            'appointment_id',
            'name',
            'purpose',
            'drug',
            'drug_id',
            'dosage',
            'repeat_days',
            'repeat_time',
        ]
        read_only_fields = ['id', 'appointment', 'drug']

