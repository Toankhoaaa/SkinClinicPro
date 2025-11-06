from django.shortcuts import render
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication

from doctor.models import Doctor
from doctor.serializers import DoctorSerializer


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@authentication_classes([JWTAuthentication])
def myProfileView(request):
    """
    API endpoint to get detailed doctor profile information
    Returns doctor data including user information
    """
    try:
        doctor = Doctor.objects.get(user=request.user)

        serializer = DoctorSerializer(doctor)

        return Response({
            'success': True,
            'message': 'Doctor profile retrieved successfully',
            'data': serializer.data
        }, status=status.HTTP_200_OK)


    except Doctor.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Patient profile not found',
            'error': 'No patient profile exists for this user'
        }, status=status.HTTP_404_NOT_FOUND)

    except Exception as e:
        return Response({
            'success': False,
            'message': 'An error occurred while retrieving doctor profile',
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)