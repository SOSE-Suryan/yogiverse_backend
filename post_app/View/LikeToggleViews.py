from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.contrib.contenttypes.models import ContentType
from post_app.models import Like, Comment
from post_app.Serializer.LikeSerializer import LikeSerializer

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


