from django.shortcuts import render
from user_app.models import *
from rest_framework.views import APIView
from user_app.serializers import FCMTokenSerializer
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction
import ast
from firebase_admin import messaging
import logging
from follower_app.firebase_config import initialize_firebase, send_notification, validate_token
import time
from rest_framework.permissions import IsAuthenticated

# Set up logger
logger = logging.getLogger(__name__)

class FCMTokenView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            # Get token from request data
            token = request.data.get('token')
            if not token:
                return Response({'error': 'Token is required'}, status=status.HTTP_400_BAD_REQUEST)

            # Initialize Firebase
            app = initialize_firebase()
            logger.info(f"Using Firebase project ID: {app.project_id}")

            # Validate token
            if not validate_token(token):
                return Response({
                    'error': 'Invalid token',
                    'details': 'The token is not registered with Firebase. Please ensure you are using the correct Firebase project configuration in your app.',
                    'project_id': app.project_id
                }, status=status.HTTP_400_BAD_REQUEST)

            # If token is valid, save it
            serializer = FCMTokenSerializer(data=request.data, context={'user': request.user})
            if serializer.is_valid():
                token_instance = serializer.save()
                
                # Send a success notification
                try:
                    send_notification(
                        user=request.user,
                        title='Token Registered',
                        body='Your device has been successfully registered for notifications'
                    )
                except Exception as e:
                    logger.error(f"Failed to send success notification: {str(e)}")
                
                return Response({
                    'message': 'Token registered successfully',
                    'token': token_instance.token,
                    'device_type': token_instance.device_type,
                    'device_name': token_instance.device_name
                }, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            logger.error(f"Error in FCMTokenView: {str(e)}")
            return Response({
                'error': 'Internal server error',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    