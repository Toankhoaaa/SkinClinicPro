# doctor/views.py

from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.decorators import action  # Import 'action'

from .models import Doctor
from .serializers import DoctorSerializer

class DoctorViewSet(viewsets.ModelViewSet):
    """
    ViewSet để quản lý Bác sĩ.
    - Cung cấp các hành động CRUD (List, Retrieve, Update, ...).
    - Cung cấp hành động tùy chỉnh 'my-profile' để bác sĩ tự xem hồ sơ.
    """
    
    # 1. CẤU HÌNH CHUNG
    serializer_class = DoctorSerializer
    
    # Lấy tất cả bác sĩ đã được xác minh và có sẵn
    queryset = Doctor.objects.filter(
        is_available=True, 
        verificationStatus="VERIFIED"
    )
    
    # Áp dụng cho TẤT CẢ các hành động trong ViewSet này
    authentication_classes = [JWTAuthentication]
    
    # 2. QUYỀN HẠN (Permissions) - Tùy chỉnh theo hành động
    
    def get_permissions(self):
        """
        Gán quyền (permissions) khác nhau cho các hành động khác nhau.
        """
        if self.action in ['list', 'retrieve']:
            # Bất kỳ ai đã đăng nhập (ví dụ: Patient) đều có thể
            # xem danh sách và chi tiết bác sĩ.
            self.permission_classes = [IsAuthenticated]
        elif self.action == 'my_profile':
            # Chỉ người đã đăng nhập mới xem được 'my-profile'
            self.permission_classes = [IsAuthenticated]
        else:
            # Chỉ Admin mới được phép tạo, sửa, xóa bác sĩ
            # (create, update, partial_update, destroy)
            self.permission_classes = [IsAdminUser]
            
        return super().get_permissions()

    # 3. HÀNH ĐỘNG TÙY CHỈNH (Custom Action)
    # Đây chính là logic từ 'myProfileView' của bạn

    @action(detail=False, methods=['get'], url_path='my-profile')
    def my_profile(self, request):
        """
        API endpoint để bác sĩ (đang đăng nhập)
        lấy thông tin hồ sơ chi tiết của chính mình.
        """
        try:
            # 'self.request.user' thay cho 'request.user'
            doctor = Doctor.objects.get(user=self.request.user)

            # 'self.get_serializer' thay cho 'DoctorSerializer'
            # để ViewSet có thể truyền context (ví dụ: request)
            serializer = self.get_serializer(doctor)

            return Response({
                'success': True,
                'message': 'Doctor profile retrieved successfully',
                'data': serializer.data
            }, status=status.HTTP_200_OK)

        except Doctor.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Doctor profile not found',
                'error': 'No doctor profile exists for this user'
            }, status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            return Response({
                'success': False,
                'message': 'An error occurred while retrieving doctor profile',
                'error': str(e) # Thêm chi tiết lỗi
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)