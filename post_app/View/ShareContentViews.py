from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from post_app.models import Post, Reel
from django.conf import settings

class ShareContentAPIView(APIView):
    def get(self, request, *args, **kwargs):
        content_type = request.query_params.get('type')  # 'post' or 'reel'
        object_id = request.query_params.get('id')

        if content_type not in ['post', 'reel'] or not object_id:
            return Response({"success": False, "message": "Invalid or missing parameters"}, status=400)

        model = Post if content_type == 'post' else Reel

        try:
            instance = model.objects.get(id=object_id)
        except model.DoesNotExist:
            return Response({"success": False, "message": f"{content_type.capitalize()} not found"}, status=404)

        # You can define the base URL in settings or hardcode it
        base_url = request.META.get('HTTP_REFERER', None)            
        share_url = f"{base_url}/{content_type}s/{instance.slug}/"

        return Response({
            "success": True,
            "message": f"{content_type.capitalize()} share link generated successfully",
            "data": {"share_url": share_url}
        }, status=200)
