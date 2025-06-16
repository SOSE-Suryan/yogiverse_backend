from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from django.contrib.auth import get_user_model
from .models import Follower, FirebaseNotification
from .serializers import FollowerSerializer, FirebaseNotificationSerializer
from .firebase_config import send_notification, initialize_firebase, get_user_fcm_tokens, validate_token
from user_app.models import FCMTokenModel
from firebase_admin import messaging
import logging
import time
from django.db.models import Q

logger = logging.getLogger(__name__)
User = get_user_model()

class StandardResultsSetPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100

class FollowUserView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user_to_follow_id = request.data.get('user_id')
        if not user_to_follow_id:
            return Response({'error': 'user_id is required'}, status=status.HTTP_400_BAD_REQUEST)

        user_to_follow = get_object_or_404(User, id=user_to_follow_id)
        
        if user_to_follow == request.user:
            return Response({'error': 'You cannot follow yourself'}, status=status.HTTP_400_BAD_REQUEST)

        # Check if already following
        if Follower.objects.filter(follower=request.user, following=user_to_follow).exists():
            return Response({'error': 'Already following this user'}, status=status.HTTP_400_BAD_REQUEST)

        # Create the follow relationship
        follower = Follower.objects.create(
            follower=request.user,
            following=user_to_follow
        )

        # Create notification in database
        notification = FirebaseNotification.objects.create(
            user=user_to_follow,
            title='New Follower',
            body=f'{request.user.username} started following you',
            data={
                'type': 'follow',
                'follower_id': str(request.user.id),
                'follower_name': request.user.username,
                'follower_profile_picture': request.user.profile.profile_picture.url if hasattr(request.user, 'profile') and request.user.profile.profile_picture else None
            }
        )

        # Send push notification
        try:
            # Initialize Firebase
            initialize_firebase()
            
            # Get FCM tokens for the user being followed
            tokens = get_user_fcm_tokens(user_to_follow)
            
            if tokens:
                # Send notification to each token
                for token in tokens:
                    try:
                        message = messaging.Message(
                            notification=messaging.Notification(
                                title='New Follower',
                                body=f'{request.user.username} started following you',
                                image=request.user.profile.profile_picture.url if hasattr(request.user, 'profile') and request.user.profile.profile_picture else None
                            ),
                            data={
                                'type': 'follow',
                                'follower_id': str(request.user.id),
                                'follower_name': request.user.username,
                                'notification_id': str(notification.id),
                                'timestamp': str(int(time.time()))
                            },
                            token=token,
                            android=messaging.AndroidConfig(
                                priority='high',
                                notification=messaging.AndroidNotification(
                                    priority='high',
                                    sound='default'
                                )
                            ),
                            apns=messaging.APNSConfig(
                                payload=messaging.APNSPayload(
                                    aps=messaging.Aps(
                                        sound='default',
                                        badge=1
                                    )
                                )
                            )
                        )
                        
                        # Send the message
                        messaging.send(message)
                        logger.info(f"Successfully sent follow notification to token: {token}")
                        
                    except Exception as e:
                        error_message = str(e)
                        logger.error(f"Failed to send follow notification to token {token}: {error_message}")
            else:
                logger.warning(f"No FCM tokens found for user {user_to_follow.username}")
                
        except Exception as e:
            logger.error(f"Error sending follow notification: {str(e)}")

        return Response(FollowerSerializer(follower).data, status=status.HTTP_201_CREATED)

class UnfollowUserView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user_to_unfollow_id = request.data.get('user_id')
        if not user_to_unfollow_id:
            return Response({'error': 'user_id is required'}, status=status.HTTP_400_BAD_REQUEST)

        user_to_unfollow = get_object_or_404(User, id=user_to_unfollow_id)
        
        # Check if following
        follower = Follower.objects.filter(follower=request.user, following=user_to_unfollow).first()
        if not follower:
            return Response({'error': 'Not following this user'}, status=status.HTTP_400_BAD_REQUEST)

        # Delete the follow relationship
        follower.delete()

        return Response({'message': 'Successfully unfollowed user'}, status=status.HTTP_200_OK)

class FollowingListView(APIView):
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    def get(self, request):
        following = Follower.objects.filter(follower=request.user)
        
        # Apply pagination
        paginator = self.pagination_class()
        paginated_following = paginator.paginate_queryset(following, request)
        
        serializer = FollowerSerializer(paginated_following, many=True)
        return paginator.get_paginated_response(serializer.data)

class FollowersListView(APIView):
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    def get(self, request):
        followers = Follower.objects.filter(following=request.user)
        
        # Apply pagination
        paginator = self.pagination_class()
        paginated_followers = paginator.paginate_queryset(followers, request)
        
        serializer = FollowerSerializer(paginated_followers, many=True)
        return paginator.get_paginated_response(serializer.data)

class NotificationListView(APIView):
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    def get(self, request):
        notifications = FirebaseNotification.objects.filter(user=request.user)
        
        # Apply pagination
        paginator = self.pagination_class()
        paginated_notifications = paginator.paginate_queryset(notifications, request)
        
        serializer = FirebaseNotificationSerializer(paginated_notifications, many=True)
        return paginator.get_paginated_response(serializer.data)

class MarkNotificationReadView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, notification_id):
        notification = get_object_or_404(FirebaseNotification, id=notification_id, user=request.user)
        notification.is_read = True
        notification.save()
        return Response({'message': 'Notification marked as read'})

class MarkAllNotificationsReadView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        FirebaseNotification.objects.filter(user=request.user, is_read=False).update(is_read=True)
        return Response({'message': 'All notifications marked as read'})

class UpdateFCMTokenView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            token = request.data.get('token')
            device_type = request.data.get('device_type', 'web')
            device_name = request.data.get('device_name', 'Unknown Device')
            
            if not token:
                return Response({
                    'error': 'Token is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Initialize Firebase
            initialize_firebase()
            
            # Create new token entry
            fcm_token = FCMTokenModel.objects.create(
                user=request.user,
                token=token,
                device_type=device_type,
                device_name=device_name
            )
            
            # Send a simple test notification
            try:
                message = messaging.Message(
                    notification=messaging.Notification(
                        title='Test Notification',
                        body='This is a test notification'
                    ),
                    token=token
                )
                messaging.send(message)
                logger.info("Test notification sent successfully")
            except Exception as e:
                logger.error(f"Failed to send test notification: {str(e)}")
            
            return Response({
                'message': 'Token registered successfully',
                'token': token,
                'device_type': device_type,
                'device_name': device_name
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"Error registering FCM token: {str(e)}")
            return Response({
                'error': 'Failed to register token',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR) 