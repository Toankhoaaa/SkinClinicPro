from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AppointmentViewSet

router = DefaultRouter()
router.register(r'appointments', AppointmentViewSet, basename='appointment')

urlpatterns = [
    path('', include(router.urls)),
]

# ----- CÁC ENDPOINTS SẼ ĐƯỢC TẠO RA -----
# GET /api/appointments/                  -> List (danh sách lịch hẹn của user)
# POST /api/appointments/                 -> Create (tạo lịch hẹn mới)
#
# GET /api/appointments/{id}/             -> Retrieve (chi tiết 1 lịch hẹn)
# PUT /api/appointments/{id}/             -> Update (cập nhật toàn bộ)
# PATCH /api/appointments/{id}/           -> Partial Update (cập nhật 1 phần)
# DELETE /api/appointments/{id}/         -> Delete (xóa 1 lịch hẹn)
#
# ----- CÁC CUSTOM ACTIONS -----
# PATCH /api/appointments/{id}/cancel/    -> Hủy lịch hẹn (cho Patient)
# PATCH /api/appointments/{id}/confirm/   -> Xác nhận lịch hẹn (cho Doctor)
# PATCH /api/appointments/{id}/complete/  -> Hoàn thành lịch hẹn (cho Doctor)