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
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

logger = logging.getLogger(__name__)
User = get_user_model()

def send_follow_count_updates(user_id):
    """
    Send WebSocket updates for both followers and following counts
    """
    try:
        channel_layer = get_channel_layer()
        followers_count = Follower.objects.filter(following_id=user_id, status='approved').count()
        following_count = Follower.objects.filter(follower_id=user_id, status='approved').count()
        
        # Send to followers group
        async_to_sync(channel_layer.group_send)(
            f"followers_{user_id}",
            {
                "type": "follow_count_update",
                "followers_count": followers_count,
                "following_count": following_count
            }
        )
        
        # Send to following group
        async_to_sync(channel_layer.group_send)(
            f"following_{user_id}",
            {
                "type": "follow_count_update",
                "followers_count": followers_count,
                "following_count": following_count
            }
        )
        
        logger.info(f"Sent follow count updates to user {user_id}: followers={followers_count}, following={following_count}")
    except Exception as e:
        logger.error(f"Error sending follow count updates: {str(e)}")

class StandardResultsSetPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100

    def get_paginated_response(self, data):
        return Response({
            'success': True,
            'message': 'Results retrieved successfully',
            'data': {
                'count': self.page.paginator.count,
                'next': self.get_next_link(),
                'previous': self.get_previous_link(),
                'results': data
            }
        })

class FollowUserView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user_to_follow_id = request.data.get('user_id')
        if not user_to_follow_id:
            return Response({
                'success': False,
                'message': 'user_id is required',
                'data': None
            }, status=status.HTTP_400_BAD_REQUEST)

        user_to_follow = get_object_or_404(User, id=user_to_follow_id)
        
        if user_to_follow == request.user:
            return Response({
                'success': False,
                'message': 'You cannot follow yourself',
                'data': None
            }, status=status.HTTP_400_BAD_REQUEST)

        # Check if already following or request exists
        existing_follow = Follower.objects.filter(follower=request.user, following=user_to_follow).first()
        if existing_follow:
            if existing_follow.status == 'approved':
                return Response({
                    'success': False,
                    'message': 'Already following this user',
                    'data': None
                }, status=status.HTTP_400_BAD_REQUEST)
            elif existing_follow.status == 'pending':
                return Response({
                    'success': False,
                    'message': 'Follow request already pending',
                    'data': None
                }, status=status.HTTP_400_BAD_REQUEST)
            elif existing_follow.status == 'rejected':
                existing_follow.status = 'pending'
                existing_follow.save()
                # Send WebSocket updates
                send_follow_count_updates(user_to_follow.id)
                return Response({
                    'success': True,
                    'message': 'Follow request resubmitted',
                    'data': FollowerSerializer(existing_follow).data
                }, status=status.HTTP_200_OK)

        # Create the follow relationship with pending status
        follower = Follower.objects.create(
            follower=request.user,
            following=user_to_follow,
            status='pending'
        )

        # Send WebSocket updates
        send_follow_count_updates(user_to_follow.id)

        # Create notification in database
        notification = FirebaseNotification.objects.create(
            user=user_to_follow,
            title='New Follow Request',
            body=f'{request.user.username} wants to follow you',
            data={
                'type': 'follow_request',
                'follower_id': str(request.user.id),
                'follower_name': request.user.username,
                'follower_profile_picture': request.user.profile.profile_picture.url if hasattr(request.user, 'profile') and request.user.profile.profile_picture else None,
                'request_id': str(follower.id)
            }
        )

        # Send push notification
        try:
            initialize_firebase()
            tokens = get_user_fcm_tokens(user_to_follow)
            
            if tokens:
                for token in tokens:
                    try:
                        message = messaging.Message(
                            notification=messaging.Notification(
                                title='New Follow Request',
                                body=f'{request.user.username} wants to follow you',
                                image=request.user.profile.profile_picture.url if hasattr(request.user, 'profile') and request.user.profile.profile_picture else None
                            ),
                            data={
                                'type': 'follow_request',
                                'follower_id': str(request.user.id),
                                'follower_name': request.user.username,
                                'notification_id': str(notification.id),
                                'request_id': str(follower.id),
                                'timestamp': str(int(time.time()))
                            },
                            token=token
                        )
                        messaging.send(message)
                        logger.info(f"Successfully sent follow request notification to token: {token}")
                    except Exception as e:
                        logger.error(f"Failed to send follow request notification to token {token}: {str(e)}")
        except Exception as e:
            logger.error(f"Error sending follow request notification: {str(e)}")

        return Response({
            'success': True,
            'message': 'Follow request sent successfully',
            'data': FollowerSerializer(follower).data
        }, status=status.HTTP_201_CREATED)

class HandleFollowRequestView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        request_id = request.data.get('request_id')
        action = request.data.get('action')

        if not request_id or not action:
            return Response({
                'success': False,
                'message': 'request_id and action are required',
                'data': None
            }, status=status.HTTP_400_BAD_REQUEST)

        if action not in ['approve', 'reject']:
            return Response({
                'success': False,
                'message': 'action must be either approve or reject',
                'data': None
            }, status=status.HTTP_400_BAD_REQUEST)

        follow_request = get_object_or_404(Follower, id=request_id, following=request.user, status='pending')

        if action == 'approve':
            follow_request.status = 'approved'
            follow_request.save()

            # Send WebSocket updates for both users
            send_follow_count_updates(request.user.id)
            send_follow_count_updates(follow_request.follower.id)

            # Create notification for the follower
            notification = FirebaseNotification.objects.create(
                user=follow_request.follower,
                title='Follow Request Approved',
                body=f'{request.user.username} approved your follow request',
                data={
                    'type': 'follow_request_approved',
                    'following_id': str(request.user.id),
                    'following_name': request.user.username,
                    'following_profile_picture': request.user.profile.profile_picture.url if hasattr(request.user, 'profile') and request.user.profile.profile_picture else None
                }
            )

            # Send push notification
            try:
                initialize_firebase()
                tokens = get_user_fcm_tokens(follow_request.follower)
                
                if tokens:
                    for token in tokens:
                        try:
                            message = messaging.Message(
                                notification=messaging.Notification(
                                    title='Follow Request Approved',
                                    body=f'{request.user.username} approved your follow request',
                                    image=request.user.profile.profile_picture.url if hasattr(request.user, 'profile') and request.user.profile.profile_picture else None
                                ),
                                data={
                                    'type': 'follow_request_approved',
                                    'following_id': str(request.user.id),
                                    'following_name': request.user.username,
                                    'notification_id': str(notification.id),
                                    'timestamp': str(int(time.time()))
                                },
                                token=token
                            )
                            messaging.send(message)
                            logger.info(f"Successfully sent follow request approval notification to token: {token}")
                        except Exception as e:
                            logger.error(f"Failed to send follow request approval notification to token {token}: {str(e)}")
            except Exception as e:
                logger.error(f"Error sending follow request approval notification: {str(e)}")

            return Response({
                'success': True,
                'message': 'Follow request approved successfully',
                'data': FollowerSerializer(follow_request).data
            }, status=status.HTTP_200_OK)

        else:  # reject
            follow_request.status = 'rejected'
            follow_request.save()
            send_follow_count_updates(request.user.id)

            return Response({
                'success': True,
                'message': 'Follow request rejected successfully',
                'data': FollowerSerializer(follow_request).data
            }, status=status.HTTP_200_OK)

class UnfollowUserView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user_to_unfollow_id = request.data.get('user_id')
        if not user_to_unfollow_id:
            return Response({
                'success': False,
                'message': 'user_id is required',
                'data': None
            }, status=status.HTTP_400_BAD_REQUEST)

        user_to_unfollow = get_object_or_404(User, id=user_to_unfollow_id)
        
        follower = Follower.objects.filter(follower=request.user, following=user_to_unfollow).first()
        if not follower:
            return Response({
                'success': False,
                'message': 'Not following this user',
                'data': None
            }, status=status.HTTP_400_BAD_REQUEST)

        follower.delete()
        send_follow_count_updates(request.user.id)
        send_follow_count_updates(user_to_unfollow.id)

        return Response({
            'success': True,
            'message': 'Successfully unfollowed user',
            'data': None
        }, status=status.HTTP_200_OK)

class FollowingListView(APIView):
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    def get(self, request,id=None):
        
        # user_id = id if id is not None else request.user.id  
        # user = request.user
        # if id is not None:
        #     from django.contrib.auth import get_user_model
        #     User = get_user_model()
        #     try:
        #         user = User.objects.get(id=id)
        #     except User.DoesNotExist:
        #         return Response({'detail': 'User not found.'}, status=404)       
        # print(request.user,type(reques)
        # print(user)   
        following = Follower.objects.filter(follower=request.user, status='approved')
        paginator = self.pagination_class()
        paginated_following = paginator.paginate_queryset(following, request)
        serializer = FollowerSerializer(paginated_following, many=True)
        return paginator.get_paginated_response(serializer.data)

class FollowersListView(APIView):
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    def get(self, request):
        # user_id = id if id is not None else request.user.id
        # user = request.user
        # if id is not None:
        #     from django.contrib.auth import get_user_model
        #     User = get_user_model()
        #     try:
        #         user = User.objects.get(id=id)
        #     except User.DoesNotExist:
        #         return Response({'detail': 'User not found.'}, status=404)
        followers = Follower.objects.filter(following=request.user, status='approved')
        paginator = self.pagination_class()
        paginated_followers = paginator.paginate_queryset(followers, request)
        serializer = FollowerSerializer(paginated_followers, many=True)
        return paginator.get_paginated_response(serializer.data)

class PendingFollowRequestsView(APIView):
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    def get(self, request):
        pending_requests = Follower.objects.filter(following=request.user, status='pending')
        paginator = self.pagination_class()
        paginated_requests = paginator.paginate_queryset(pending_requests, request)
        serializer = FollowerSerializer(paginated_requests, many=True)
        return paginator.get_paginated_response(serializer.data)

class NotificationListView(APIView):
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    def get(self, request):
        notifications = FirebaseNotification.objects.filter(user=request.user)
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
        return Response({
            'success': True,
            'message': 'Notification marked as read',
            'data': FirebaseNotificationSerializer(notification).data
        }, status=status.HTTP_200_OK)

class MarkAllNotificationsReadView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        FirebaseNotification.objects.filter(user=request.user, is_read=False).update(is_read=True)
        return Response({
            'success': True,
            'message': 'All notifications marked as read',
            'data': None
        }, status=status.HTTP_200_OK)

class UpdateFCMTokenView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        token = request.data.get('token')
        if not token:
            return Response({
                'success': False,
                'message': 'token is required',
                'data': None
            }, status=status.HTTP_400_BAD_REQUEST)

        FCMTokenModel.objects.update_or_create(
            user=request.user,
            defaults={'token': token}
        )

        return Response({
            'success': True,
            'message': 'FCM token updated successfully',
            'data': None
        }, status=status.HTTP_200_OK) 