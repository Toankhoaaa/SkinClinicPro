# patients/views.py

from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.decorators import action

from .models import Patient
from .serializers import PatientSerializer

class PatientViewSet(viewsets.ModelViewSet):
    """
    ViewSet để quản lý Bệnh nhân (Patient).
    - Endpoint chuẩn (list, retrieve, update, delete): Dành cho Admin.
    - Endpoint tùy chỉnh 'me' (GET, PUT, PATCH, DELETE): Dành cho 
      bệnh nhân tự quản lý hồ sơ của mình.
    """
    
    # --- Cấu hình chung ---
    serializer_class = PatientSerializer
    queryset = Patient.objects.all() # Dành cho Admin
    authentication_classes = [JWTAuthentication]

    def get_permissions(self):
        """
        Gán quyền (permissions) khác nhau cho các hành động khác nhau:
        - Admin: Có full quyền CRUD trên tất cả bệnh nhân.
        - Authenticated User: Chỉ có quyền trên action 'me'.
        """
        if self.action == 'me':
            self.permission_classes = [IsAuthenticated]
        else:
            self.permission_classes = [IsAdminUser] # Admin mới được list/get/update bệnh nhân khác
        return super().get_permissions()

    # --- GỘP CẢ 3 VIEW CỦA BẠN VÀO ĐÂY ---
    
    @action(detail=False, methods=['get', 'put', 'patch', 'delete'], url_path='me')
    def me(self, request, *args, **kwargs):
        """
        Endpoint thống nhất cho bệnh nhân tự quản lý hồ sơ.
        - GET /api/patients/me/: Lấy hồ sơ
        - PUT/PATCH /api/patients/me/: Cập nhật hồ sơ
        - DELETE /api/patients/me/: Xóa hồ sơ
        """
        try:
            # Lấy patient từ user đang đăng nhập
            patient = Patient.objects.get(user=request.user)
        except Patient.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Patient profile not found',
                'error': 'No patient profile exists for this user'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                'success': False,
                'message': 'An error occurred',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # ---------------------------------
        # 1. Logic cho GET (myProfileView)
        # ---------------------------------
        if request.method == 'GET':
            serializer = self.get_serializer(patient)
            return Response({
                'success': True,
                'message': 'Patient profile retrieved successfully',
                'data': serializer.data
            }, status=status.HTTP_200_OK)

        # ---------------------------------
        # 2. Logic cho PUT/PATCH (updateProfileView)
        # ---------------------------------
        elif request.method == 'PUT' or request.method == 'PATCH':
            # 'partial=True' cho phép cập nhật 1 phần (PATCH)
            # và cũng hoạt động cho PUT nếu gửi đủ data.
            serializer = self.get_serializer(patient, data=request.data, partial=True)
            
            if serializer.is_valid():
                serializer.save()
                return Response({
                    'success': True,
                    'message': 'Patient profile updated successfully',
                    'data': serializer.data
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'success': False,
                    'message': 'Invalid data provided',
                    'errors': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)

        # ---------------------------------
        # 3. Logic cho DELETE (deleteProfileView)
        # ---------------------------------
        elif request.method == 'DELETE':
            # Xóa user, profile (Patient) sẽ tự động bị xóa
            # do 'on_delete=models.CASCADE' trên 'user' field.
            user = request.user
            user.delete()
            return Response({
                'success': True,
                'message': 'Patient profile and associated user account deleted successfully'
            }, status=status.HTTP_200_OK)
            
        # Fallback (phòng trường hợp method không mong muốn)
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)