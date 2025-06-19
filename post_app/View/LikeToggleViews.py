from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.contrib.contenttypes.models import ContentType
from post_app.models import Like
from post_app.Serializer.LikeSerializer import LikeSerializer
from itertools import chain
from follower_app.models import FirebaseNotification
from follower_app.firebase_config import initialize_firebase, get_user_fcm_tokens
from firebase_admin import messaging
import time
import logging

logger = logging.getLogger(__name__)

class LikeToggleAPIView(generics.GenericAPIView):
    serializer_class = LikeSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        content_type = request.data.get('content_type')
        object_id = request.data.get('object_id')

        try:
            model = ContentType.objects.get(model=content_type).model_class()
            obj = model.objects.get(id=object_id)
        except ContentType.DoesNotExist:
            return Response({"detail": "Invalid content type"}, status=400)
        except model.DoesNotExist:
            return Response({"detail": "Object not found"}, status=404)

        content_type_obj = ContentType.objects.get_for_model(obj)
        like, created = Like.objects.get_or_create(
            user=user,
            content_type=content_type_obj,
            object_id=obj.id
        )

        if not created:
            like.delete()
            return Response({"success": True, "message": "Unliked"}, status=200)

        # ✅ Send Push Notification to Object Owner (if not self-like)
        owner = getattr(obj, 'user', None)

        if owner and owner != user:
            try:
                # Create database notification
                notification = FirebaseNotification.objects.create(
                    user=owner,
                    title='New Like',
                    body=f'{user.username} liked your post',
                    data={
                        'type': 'like',
                        'liker_id': str(user.id),
                        'liker_name': user.username,
                        'liker_profile_picture': user.profile.profile_picture.url if hasattr(user, 'profile') and user.profile.profile_picture else None,
                        'content_type': content_type,
                        'object_id': str(object_id),
                    }
                )

                initialize_firebase()
                tokens = get_user_fcm_tokens(owner)

                if tokens:
                    for token in tokens:
                        try:
                            message = messaging.Message(
                                notification=messaging.Notification(
                                    title='New Like',
                                    body=f'{user.username} liked your post',
                                    image=user.profile.profile_picture.url if hasattr(user, 'profile') and user.profile.profile_picture else None
                                ),
                                data={
                                    'type': 'like',
                                    'liker_id': str(user.id),
                                    'liker_name': user.username,
                                    'notification_id': str(notification.id),
                                    'object_id': str(object_id),
                                    'content_type': content_type,
                                    'timestamp': str(int(time.time()))
                                },
                                token=token
                            )
                            messaging.send(message)
                            logger.info(f"Successfully sent like notification to token: {token}")
                        except Exception as e:
                            logger.error(f"Failed to send like notification to token {token}: {str(e)}")
            except Exception as e:
                logger.error(f"Error sending like notification: {str(e)}")

        return Response({"success": True, "message": "Liked"}, status=201)



class LikeListAPIView(generics.ListAPIView):
    serializer_class = LikeSerializer
    # permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        content_type = request.query_params.get('content_type')
        object_id = request.query_params.get('object_id')

        if not content_type or not object_id:
            return Response({"success": False, "message": "Content type and object ID are required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            content_type_obj = ContentType.objects.get(model=content_type.lower())
        except ContentType.DoesNotExist:
            return Response({"success": False, "message": "Invalid content type"}, status=status.HTTP_400_BAD_REQUEST)

        # Get likes by authenticated user first (if any)
        if request.user and request.user.is_authenticated:
            user_likes = Like.objects.filter(
                content_type=content_type_obj,
                object_id=object_id,
                user=request.user
            ).order_by('-created_at')

            other_likes = Like.objects.filter(
                content_type=content_type_obj,
                object_id=object_id
            ).exclude(user=request.user).order_by('-created_at')

            combined_likes = list(chain(user_likes, other_likes))
        else:
            # If no authenticated user, just show all likes
            combined_likes = Like.objects.filter(
                content_type=content_type_obj,
                object_id=object_id
            ).order_by('-created_at')


        serializer = self.get_serializer(combined_likes, many=True)
        return Response({"success": True, "data": serializer.data}, status=status.HTTP_200_OK)
