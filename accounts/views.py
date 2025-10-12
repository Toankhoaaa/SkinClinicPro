from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken
from .serializers import UserSignupSerializer, UserLoginSerializer, ResetTokenSerializer
from django.contrib.auth import get_user_model
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

User = get_user_model()

@api_view(['POST'])
@permission_classes([AllowAny])
def signUpView(request):
    """
    API endpoint for user registration
    """
    serializer = UserSignupSerializer(data=request.data)
    
    if serializer.is_valid():
        user = serializer.save()
        
        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        access_token = refresh.access_token
        
        return Response({
            'message': 'Đăng ký thành công!',
            'user': {
                'id': user.id,
                'username': user.username,
                'role': user.role,
                'first_name': user.first_name,
                'last_name': user.last_name,
            },
            'tokens': {
                'refresh': str(refresh),
                'access': str(access_token),
            }
        }, status=status.HTTP_201_CREATED)
    
    return Response({
        'message': 'Đăng ký thất bại!',
        'errors': serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([AllowAny])
def loginView(request):
    """
    API endpoint for user login
    """
    serializer = UserLoginSerializer(data=request.data)
    
    if serializer.is_valid():
        user = serializer.validated_data['user']
        
        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        access_token = refresh.access_token
        
        return Response({
            'message': 'Đăng nhập thành công!',
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'phone': user.phone,
                'role': user.role,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'is_active': user.is_active,
                'date_joined': user.date_joined,
            },
            'tokens': {
                'refresh': str(refresh),
                'access': str(access_token),
            }
        }, status=status.HTTP_200_OK)
    
    return Response({
        'message': 'Đăng nhập thất bại!',
        'errors': serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)

@method_decorator(csrf_exempt, name='dispatch')
class RefreshTokenView(APIView):
    """
    API endpoint for refreshing access token using refresh token
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        try:
            # Lấy refresh token từ request body hoặc cookies
            refresh_token = request.data.get('refresh') or request.COOKIES.get('refreshToken')
            
            if not refresh_token:
                return Response({
                    'message': 'Refresh token không được cung cấp!',
                    'error': 'MISSING_REFRESH_TOKEN'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Tạo RefreshToken object từ string
            refresh = RefreshToken(refresh_token)
            
            # Lấy user từ refresh token
            user_id = refresh.payload.get('user_id')
            if not user_id:
                return Response({
                    'message': 'Refresh token không chứa thông tin user!',
                    'error': 'INVALID_REFRESH_TOKEN'
                }, status=status.HTTP_401_UNAUTHORIZED)
            
            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                return Response({
                    'message': 'User không tồn tại!',
                    'error': 'USER_NOT_FOUND'
                }, status=status.HTTP_401_UNAUTHORIZED)
            
            # Tạo access token mới
            access_token = refresh.access_token
            
            # Tạo refresh token mới (optional - để tăng bảo mật)
            new_refresh = RefreshToken.for_user(user)
            
            return Response({
                'message': 'Token được làm mới thành công!',
                'tokens': {
                    'access': str(access_token),
                    'refresh': str(new_refresh),
                }
            }, status=status.HTTP_200_OK)
            
        except TokenError as e:
            return Response({
                'message': 'Refresh token không hợp lệ!',
                'error': 'INVALID_REFRESH_TOKEN',
                'detail': str(e)
            }, status=status.HTTP_401_UNAUTHORIZED)
            
        except Exception as e:
            return Response({
                'message': 'Có lỗi xảy ra khi làm mới token!',
                'error': 'REFRESH_TOKEN_ERROR',
                'detail': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([AllowAny])
def logoutView(request):
    """
    API endpoint for user logout - blacklist refresh token
    """
    try:
        # Lấy refresh token từ request body hoặc cookies
        refresh_token = request.data.get('refresh') or request.COOKIES.get('refreshToken')
        
        if not refresh_token:
            return Response({
                'message': 'Refresh token không được cung cấp!',
                'error': 'MISSING_REFRESH_TOKEN'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Tạo RefreshToken object và blacklist nó
        refresh = RefreshToken(refresh_token)
        refresh.blacklist()
        
        return Response({
            'message': 'Đăng xuất thành công!'
        }, status=status.HTTP_200_OK)
        
    except TokenError as e:
        return Response({
            'message': 'Refresh token không hợp lệ!',
            'error': 'INVALID_REFRESH_TOKEN',
            'detail': str(e)
        }, status=status.HTTP_401_UNAUTHORIZED)
        
    except Exception as e:
        return Response({
            'message': 'Có lỗi xảy ra khi đăng xuất!',
            'error': 'LOGOUT_ERROR',
            'detail': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    