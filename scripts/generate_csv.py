import csv
import os
import sys
import django
from pathlib import Path
import datetime
from datetime import timedelta

# Setup Django
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "bookingcare.settings")
django.setup()

from faker import Faker
fake = Faker()

OUTPUT_DIR = BASE_DIR / "tests" / "data"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def generate_auth_data(count=15):
    """Sinh dữ liệu test Đăng ký (Bao gồm cả Valid và Invalid)"""
    filename = OUTPUT_DIR / "auth_data_full.csv"
    # Thêm cột 'desc' để dễ theo dõi trường hợp test
    headers = ['username', 'email', 'password', 'role_id', 'expected_status', 'desc']
    
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        
        # 1. Case Valid: Sinh 10 user hợp lệ
        for _ in range(10):
            writer.writerow({
                'username': fake.user_name(),
                'email': fake.email(),
                'password': 'Strong@Pass123!',
                'role_id': 3,
                'expected_status': 201,
                'desc': 'Valid User'
            })
            
        # 2. Case Invalid: Role không tồn tại
        writer.writerow({
            'username': 'bad_role_user',
            'email': 'bad_role@test.com',
            'password': 'Strong@Pass123!',
            'role_id': 99, 
            'expected_status': 400,
            'desc': 'Invalid Role ID'
        })

        # 3. Case Invalid: Mật khẩu quá yếu (quá ngắn)
        writer.writerow({
            'username': 'weak_pass_user',
            'email': 'weak@test.com',
            'password': '123',
            'role_id': 3,
            'expected_status': 400,
            'desc': 'Weak Password'
        })

        # 4. Case Invalid: Email sai định dạng
        writer.writerow({
            'username': 'bad_email_user',
            'email': 'not-an-email',
            'password': 'Strong@Pass123!',
            'role_id': 3,
            'expected_status': 400,
            'desc': 'Invalid Email Format'
        })

        # 5. Case Invalid: Trùng Username (Duplicate)
        # Lưu ý: username 'duplicate_user' cần được xử lý đặc biệt trong code test
        # (tạo trước 1 user tên này trong DB thì test mới Pass)
        writer.writerow({
            'username': 'duplicate_user',
            'email': 'dup@test.com',
            'password': 'Strong@Pass123!',
            'role_id': 3,
            'expected_status': 400,
            'desc': 'Duplicate Username'
        })

    print(f"✅ Đã tạo: {filename} với đầy đủ các case lỗi.")

# ... (Giữ nguyên các hàm generate_schedule_data và generate_booking_data cũ) ...

if __name__ == "__main__":
    generate_auth_data()
    # generate_schedule_data()
    # generate_booking_data()