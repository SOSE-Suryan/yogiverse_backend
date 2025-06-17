from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.contrib.contenttypes.models import ContentType
from post_app.models import Like, Comment
from post_app.Serializer.LikeSerializer import LikeSerializer
from itertools import chain


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
