# availability/serializers.py
from rest_framework import serializers
from .models import Schedule
import datetime

class ScheduleSerializer(serializers.ModelSerializer):
    
    # Thêm trường read-only để hiển thị tên bác sĩ
    doctor_name = serializers.CharField(source='doctor.user.get_full_name', read_only=True)

    class Meta:
        model = Schedule
        fields = [
            'id', 'doctor', 'doctor_name', 'date', 'start_time', 
            'end_time', 'is_available', 'max_patients'
        ]
        # Bác sĩ không cần tự chọn mình, hệ thống sẽ tự gán
        read_only_fields = ('doctor',) 

    def validate(self, data):
        if data['date'] < datetime.date.today():
            raise serializers.ValidationError("Không thể tạo lịch cho ngày trong quá khứ.")
            
        if data['start_time'] >= data['end_time']:
            raise serializers.ValidationError("Giờ kết thúc phải sau giờ bắt đầu.")
            
        return data