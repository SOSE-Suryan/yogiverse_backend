from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from django.db.models import Q, Count
from post_app.models import Post, Reel, Tag
from post_app.Serializer.PostSerializer import PostSerializer
from post_app.Serializer.ReelSerializer import ReelSerializer

class RelatedContentAPIView(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request, *args, **kwargs):
        content_type = request.query_params.get('type')  # post or reel
        object_id = request.query_params.get('id')

        if content_type not in ['post', 'reel'] or not object_id:
            return Response({"success": False, "message": "Invalid or missing parameters"}, status=400)

        model = Post if content_type == 'post' else Reel
        serializer_class = PostSerializer if content_type == 'post' else ReelSerializer

        try:
            instance = model.objects.prefetch_related('tags').get(id=object_id)
        except model.DoesNotExist:
            return Response({"success": False, "message": f"{content_type.capitalize()} not found"}, status=404)

        # Build query for related content
        query = Q()

        # Match by caption keywords
        if instance.caption:
            keywords = instance.caption.split()
            for kw in keywords:
                query |= Q(caption__icontains=kw)

        # Match by same music (for reels)
        if content_type == 'reel' and instance.music_track:
            query |= Q(music_track__icontains=instance.music_track)

        # Match by same creator
        query |= Q(user=instance.user)

        # Match by shared tags
        tag_ids = instance.tags.values_list('id', flat=True)
        if tag_ids:
            query |= Q(tags__in=tag_ids)

        # Get related content excluding self
        related_items = model.objects.filter(query).exclude(id=instance.id).distinct().annotate(
            total_likes=Count('likes', distinct=True),
            total_comments=Count('comments', distinct=True)
        ).order_by('-total_likes', '-created_at')[:12]

        serializer = serializer_class(related_items, many=True)
        return Response({
            "success": True,
            "message": "Related content fetched successfully",
            "data": serializer.data
        }, status=200)
