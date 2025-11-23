from locust import HttpUser, task, between, events
import random
import json
from datetime import date, timedelta

# --- CẤU HÌNH TÀI KHOẢN MẪU (Phải tồn tại trong DB) ---
# Lưu ý: Bạn cần đảm bảo đã chạy script tạo dữ liệu hoặc tạo tay 2 user này
DOCTOR_CREDENTIALS = {"username": "drviet123", "password": "strongpassword123"}
PATIENT_CREDENTIALS = {"username": "hungtran123", "password": "strongpassword123"}

# ID Bác sĩ mục tiêu để test đặt lịch/xem lịch
TARGET_DOCTOR_ID = 1 

@events.init.add_listener
def on_locust_init(environment, **kwargs):
    print("--- BẮT ĐẦU KIỂM THỬ HIỆU NĂNG SKINCLINIC ---")
    print(f"Target Doctor ID: {TARGET_DOCTOR_ID}")

class BaseClinicUser(HttpUser):
    """Lớp cơ sở xử lý đăng nhập và lưu token"""
    abstract = True # Không chạy trực tiếp class này
    token = None
    headers = {}
    user_data = {}

    def login(self, credentials):
        response = self.client.post("/api/auth/login/", json=credentials, name="/api/auth/login/")
        if response.status_code == 200:
            self.token = response.json()['tokens']['access']
            self.headers = {
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json"
            }
            self.user_data = response.json()['user']
            return True
        else:
            print(f"Login failed for {credentials['username']}: {response.status_code}")
            return False

class DoctorBehavior(BaseClinicUser):
    """
    Mô phỏng hành vi Bác sĩ:
    - Xem lịch làm việc.
    - Xác nhận lịch hẹn.
    - Kê đơn (Treatment).
    """
    weight = 1 # Tỉ lệ xuất hiện thấp hơn bệnh nhân
    wait_time = between(2, 5)

    def on_start(self):
        if not self.login(DOCTOR_CREDENTIALS):
            self.environment.runner.quit()

    @task(3)
    def view_own_schedule(self):
        """Xem lịch làm việc của chính mình"""
        # Giả lập xem lịch ngày mai
        tomorrow = (date.today() + timedelta(days=1)).isoformat()
        self.client.get(f"/api/schedules/?date={tomorrow}", headers=self.headers, name="GET /api/schedules/")

    @task(2)
    def view_my_profile(self):
        """Xem hồ sơ cá nhân (Tương tự test_permissions)"""
        self.client.get("/api/doctors/my-profile/", headers=self.headers, name="GET /api/doctors/my-profile/")

    @task(1)
    def negative_test_booking(self):
        """
        Kiểm thử tiêu cực: Bác sĩ cố tình đặt lịch hẹn.
        Hệ thống phải trả về 403 Forbidden.
        (Đồng bộ với test_doctor_appointment_actions.py)
        """
        payload = {
            "doctor_id": TARGET_DOCTOR_ID,
            "date": (date.today() + timedelta(days=2)).isoformat(),
            "time": "09:00"
        }
        with self.client.post("/api/appointments/", json=payload, headers=self.headers, catch_response=True, name="Negative: Doctor Book Appointment") as response:
            if response.status_code == 403:
                response.success() # Đánh dấu là Pass nếu bị chặn đúng
            else:
                response.failure(f"Security Flaw! Doctor should not book. Status: {response.status_code}")

class PatientBehavior(BaseClinicUser):
    """
    Mô phỏng hành vi Bệnh nhân:
    - Tìm kiếm bác sĩ.
    - Xem slot trống.
    - Đặt lịch (Booking Flow).
    """
    weight = 3 # Tỉ lệ xuất hiện cao (nhiều bệnh nhân hơn bác sĩ)
    wait_time = between(1, 3)

    def on_start(self):
        if not self.login(PATIENT_CREDENTIALS):
            self.environment.runner.quit()

    @task(5)
    def search_doctors(self):
        """Tìm kiếm bác sĩ (Tương tự test_doctor_search.py)"""
        self.client.get("/api/doctors/", headers=self.headers, name="GET /api/doctors/")

    @task(4)
    def check_availability(self):
        """Kiểm tra lịch trống (Logic nặng nhất server)"""
        tomorrow = (date.today() + timedelta(days=1)).isoformat()
        self.client.get(
            f"/api/appointments/available-slots/?doctor_id={TARGET_DOCTOR_ID}&date={tomorrow}",
            headers=self.headers,
            name="GET /available-slots/"
        )

    @task(2)
    def book_appointment(self):
        """
        Quy trình đặt lịch (Booking Flow).
        Sử dụng random thời gian để tránh trùng lặp quá nhiều.
        """
        day = (date.today() + timedelta(days=random.randint(1, 7))).isoformat()
        hour = random.randint(8, 16)
        minute = random.choice(["00", "30"])
        
        payload = {
            "doctor_id": TARGET_DOCTOR_ID,
            "date": day,
            "time": f"{hour:02d}:{minute}"
        }
        
        # API này có thể trả về 201 (Thành công) hoặc 400 (Trùng lịch)
        # Cả 2 đều chấp nhận được trong Load Test
        with self.client.post("/api/appointments/", json=payload, headers=self.headers, catch_response=True, name="POST /api/appointments/") as response:
            if response.status_code in [201, 400]:
                response.success()
            else:
                response.failure(f"Unexpected error: {response.status_code}")

    @task(1)
    def negative_create_treatment(self):
        """
        Kiểm thử bảo mật: Bệnh nhân cố tình tự kê đơn.
        Hệ thống phải chặn 403.
        (Đồng bộ với test_treatments.py)
        """
        payload = {
            "appointment_id": 1, # Fake ID
            "name": "Hacker Prescription"
        }
        with self.client.post("/api/treatments/", json=payload, headers=self.headers, catch_response=True, name="Negative: Patient Create Treatment") as response:
            if response.status_code == 403:
                response.success()
            else:
                response.failure(f"Security Flaw! Patient should not create treatment. Status: {response.status_code}")