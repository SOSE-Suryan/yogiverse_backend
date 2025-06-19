from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.contrib.contenttypes.models import ContentType
from post_app.models import Like, Comment
from post_app.Serializer.CommentSerializer import CommentSerializer
from itertools import chain
from follower_app.models import FirebaseNotification
from follower_app.firebase_config import initialize_firebase, get_user_fcm_tokens
from firebase_admin import messaging
import time
import logging

logger = logging.getLogger(__name__)


class CommentListAPIView(generics.ListAPIView):
    serializer_class = CommentSerializer
    # permission_classes = [IsAuthenticated]  # Optional: remove or enable based on your needs

    def get(self, request, *args, **kwargs):
        return self.list_comments(request)

    def list_comments(self, request):
        content_type = request.query_params.get('content_type')
        object_id = request.query_params.get('object_id')

        if not content_type or not object_id:
            return Response(
                {"success": False, "message": "Content type and object ID are required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            content_type_obj = ContentType.objects.get(model=content_type.lower())
        except ContentType.DoesNotExist:
            return Response(
                {"success": False, "message": "Invalid content type"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if request.user and request.user.is_authenticated:
            user_comments = Comment.objects.filter(
                content_type=content_type_obj,
                object_id=object_id,
                user=request.user
            ).order_by('-created_at')

            other_comments = Comment.objects.filter(
                content_type=content_type_obj,
                object_id=object_id
            ).exclude(user=request.user).order_by('-created_at')

            combined_comments = list(chain(user_comments, other_comments))
        else:
            combined_comments = Comment.objects.filter(
                content_type=content_type_obj,
                object_id=object_id
            ).order_by('-created_at')

        serializer = self.get_serializer(combined_comments, many=True)
        return Response({"success": True, "data": serializer.data}, status=status.HTTP_200_OK)
    


class CommentCreateAPIView(generics.CreateAPIView):
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        return self.create_comment(request)

    def create_comment(self, request):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            comment = serializer.save(user=request.user)

            # 🔍 Determine the content object (Post/Reel/etc.)
            content_type = comment.content_type
            object_id = comment.object_id
            model_class = content_type.model_class()

            try:
                content_obj = model_class.objects.get(id=object_id)
                owner = getattr(content_obj, 'user', None)  # Adjust if field is 'author' or 'owner'

                if owner and owner != request.user:
                    # ✅ Create notification in DB
                    notification = FirebaseNotification.objects.create(
                        user=owner,
                        title='New Comment',
                        body=f'{request.user.username} commented on your post',
                        data={
                            'type': 'comment',
                            'commenter_id': str(request.user.id),
                            'commenter_name': request.user.username,
                            'commenter_profile_picture': request.user.profile.profile_picture.url if hasattr(request.user, 'profile') and request.user.profile.profile_picture else None,
                            'content_type': content_type.model,
                            'object_id': str(object_id),
                            'comment_id': str(comment.id)
                        }
                    )

                    # ✅ Send push notification
                    try:
                        initialize_firebase()
                        tokens = get_user_fcm_tokens(owner)

                        if tokens:
                            for token in tokens:
                                try:
                                    message = messaging.Message(
                                        notification=messaging.Notification(
                                            title='New Comment',
                                            body=f'{request.user.username} commented on your post',
                                            image=request.user.profile.profile_picture.url if hasattr(request.user, 'profile') and request.user.profile.profile_picture else None
                                        ),
                                        data={
                                            'type': 'comment',
                                            'commenter_id': str(request.user.id),
                                            'commenter_name': request.user.username,
                                            'notification_id': str(notification.id),
                                            'comment_id': str(comment.id),
                                            'object_id': str(object_id),
                                            'content_type': content_type.model,
                                            'timestamp': str(int(time.time()))
                                        },
                                        token=token
                                    )
                                    messaging.send(message)
                                    logger.info(f"Sent comment notification to token: {token}")
                                except Exception as e:
                                    logger.error(f"Error sending comment notification to token {token}: {str(e)}")
                    except Exception as e:
                        logger.error(f"Firebase send error: {str(e)}")

            except model_class.DoesNotExist:
                logger.warning(f"Object not found for comment target: {model_class} id={object_id}")

            return Response({
                "success": True,
                "message": "Comment added",
                "data": serializer.data
            }, status=201)

        return Response({
            "success": False,
            "message": serializer.errors
        }, status=400)


class CommentUpdateAPIView(generics.UpdateAPIView):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated]

    def patch(self, request, *args, **kwargs):
        return self.update_comment(request, *args, **kwargs)

    def update_comment(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.user != request.user:
            return Response({"success": False, "message": "Permission denied"}, status=403)
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({"success": True, "message": "Comment updated", "data": serializer.data}, status=200)
        return Response({"success": False, "message": serializer.errors}, status=400)


class CommentDeleteAPIView(generics.DestroyAPIView):
    queryset = Comment.objects.all()
    permission_classes = [IsAuthenticated]

    def delete(self, request, *args, **kwargs):
        return self.delete_comment(request, *args, **kwargs)

    def delete_comment(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.user != request.user:
            return Response({"success": False, "message": "Permission denied"}, status=403)
        instance.delete()
        return Response({"success": True, "message": "Comment deleted"}, status=200)
