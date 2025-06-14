from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.db.models import Q
from post_app.Paginations.Paginations import MainPagination
from post_app.models import Post, Reel
from post_app.Serializer.PostSerializer import PostSerializer
from post_app.Serializer.ReelSerializer import ReelSerializer

class SearchExploreAPIView(GenericAPIView):
    permission_classes = [permissions.AllowAny]
    pagination_class = MainPagination

    def get_serializer(self, *args, **kwargs):
        # Not using a single model serializer, so we skip this
        return None

    def get(self, request):
        query = request.query_params.get('search', '')
        if not query:
            return Response({"success": False, "message": "Search term is required"}, status=400)

        # Search Posts by caption, location, or tag
        post_qs = Post.objects.filter(
            Q(caption__icontains=query) |
            Q(location__icontains=query) |
            Q(tags__name__icontains=query)
        ).distinct().order_by('-created_at')

        # Search Reels by caption, music_track, or tag
        reel_qs = Reel.objects.filter(
            Q(caption__icontains=query) |
            Q(music_track__icontains=query) |
            Q(tags__name__icontains=query)
        ).distinct().order_by('-created_at')

        post_results = PostSerializer(post_qs, many=True).data
        reel_results = ReelSerializer(reel_qs, many=True).data

        combined = sorted(post_results + reel_results, key=lambda x: x['created_at'], reverse=True)

        # Pagination
        paginator = self.pagination_class()
        query_params = request.query_params.get('rows_per_page')
        paginator.page_size = int(query_params) if query_params else paginator.page_size

        page = paginator.paginate_queryset(combined, request)
        data = paginator.get_paginated_response(page)
        return Response({"success": True, "message": "Search results retrieved", "data": data}, status.HTTP_200_OK)

