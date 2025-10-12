from rest_framework import status
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import get_user_model
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework_simplejwt.authentication import JWTAuthentication
from .models import Patient
from .serializers import PatientSerializer

@api_view(['GET'])
@permission_classes([IsAuthenticated])
@authentication_classes([JWTAuthentication])
def myProfileView(request):
    """
    API endpoint to get detailed patient profile information
    Returns patient data including user information
    """
    try:
        # Get the patient profile for the authenticated user
        patient = Patient.objects.get(user=request.user)
        
        # Serialize the patient data
        serializer = PatientSerializer(patient)
        
        return Response({
            'success': True,
            'message': 'Patient profile retrieved successfully',
            'data': serializer.data
        }, status=status.HTTP_200_OK)
        
    except Patient.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Patient profile not found',
            'error': 'No patient profile exists for this user'
        }, status=status.HTTP_404_NOT_FOUND)
        
    except Exception as e:
        return Response({
            'success': False,
            'message': 'An error occurred while retrieving patient profile',
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
@authentication_classes([JWTAuthentication])
def updateProfileView(request):
    """
    API endpoint to update patient profile information
    """
    try:
        # Get the patient profile for the authenticated user
        patient = Patient.objects.get(user=request.user)
        
        # Serialize the patient data with partial update support
        serializer = PatientSerializer(patient, data=request.data, partial=True)
        
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
            
    except Patient.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Patient profile not found',
            'error': 'No patient profile exists for this user'
        }, status=status.HTTP_404_NOT_FOUND)
        
    except Exception as e:
        return Response({
            'success': False,
            'message': 'An error occurred while updating patient profile',
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
@authentication_classes([JWTAuthentication])
def deleteProfileView(request):
    """
    API endpoint to delete patient profile and associated user account
    """
    try:
        # Get the patient profile for the authenticated user
        patient = Patient.objects.get(user=request.user)
        
        # Delete the associated user account, which will also delete the patient profile
        user = request.user
        user.delete()
        
        return Response({
            'success': True,
            'message': 'Patient profile and associated user account deleted successfully'
        }, status=status.HTTP_200_OK)
        
    except Patient.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Patient profile not found',
            'error': 'No patient profile exists for this user'
        }, status=status.HTTP_404_NOT_FOUND)
        
    except Exception as e:
        return Response({
            'success': False,
            'message': 'An error occurred while deleting patient profile',
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)