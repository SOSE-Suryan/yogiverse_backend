from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.permissions import IsAuthenticated
from django.contrib.contenttypes.models import ContentType
from django.db.models import Count
from post_app.models import Post, Reel
from post_app.Serializer.PostSerializer import PostSerializer
from post_app.Serializer.ReelSerializer import ReelSerializer


class TrendingContentAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        sort_by = request.query_params.get('sort_by', 'likes')  # likes, comments, views
        content_type = request.query_params.get('type', 'post')  # post, reel
        limit = int(request.query_params.get('limit', 12))

        # Validate content type
        if content_type not in ['post', 'reel']:
            return Response({"success": False, "message": "Invalid content type. Use 'post' or 'reel'."}, status=400)

        if sort_by not in ['likes', 'comments', 'views']:
            return Response({"success": False, "message": "Invalid sort_by. Use 'likes', 'comments', or 'views'."}, status=400)

        model = Post if content_type == 'post' else Reel
        serializer_class = PostSerializer if content_type == 'post' else ReelSerializer

        # Annotate with counts
        queryset = model.objects.filter(user__role='vendor').annotate(
            total_likes=Count('likes', distinct=True),
            total_comments=Count('comments', distinct=True)
        )

        # Sorting
        if sort_by == 'likes':
            queryset = queryset.order_by('-total_likes')
        elif sort_by == 'comments':
            queryset = queryset.order_by('-total_comments')
        elif sort_by == 'views':
            queryset = queryset.order_by('-views_count')  # assumes field exists

        # Limit and serialize
        queryset = queryset[:limit]
        serializer = serializer_class(queryset, many=True)

        return Response({
            "success": True,
            "message": f"Top {limit} {content_type}s sorted by {sort_by}",
            "data": serializer.data
        }, status=200)
