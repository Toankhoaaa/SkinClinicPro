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
        """
        Validate dữ liệu, hỗ trợ cả Create (đủ field) và Update (thiếu field).
        """
        # 1. Lấy date: Ưu tiên từ data gửi lên, nếu không có thì lấy từ bản ghi cũ (instance)
        date_val = data.get('date')
        if not date_val and self.instance:
            date_val = self.instance.date

        # Chỉ validate nếu có giá trị date (tránh lỗi khi cả data và instance đều ko có - dù hiếm)
        if date_val and date_val < datetime.date.today():
            raise serializers.ValidationError("Không thể tạo/sửa lịch cho ngày trong quá khứ.")
            
        # 2. Lấy start_time và end_time tương tự
        start = data.get('start_time')
        end = data.get('end_time')
        
        if self.instance:
            start = start or self.instance.start_time
            end = end or self.instance.end_time

        # 3. Validate logic giờ
        if start and end and start >= end:
            raise serializers.ValidationError("Giờ kết thúc phải sau giờ bắt đầu.")
            
        return data