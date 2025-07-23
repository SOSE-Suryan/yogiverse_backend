from rest_framework import generics, status
from rest_framework.response import Response
from post_app.models import Post, Reel
from post_app.Serializer.PostSerializer import PostSerializer
from post_app.Serializer.ReelSerializer import ReelSerializer
from post_app.Paginations.Paginations import MainPagination
from rest_framework.permissions import IsAuthenticated
from operator import itemgetter

class DraftListAPIView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    pagination_class = MainPagination

    def get(self, request, *args, **kwargs):
        user = request.user
        
        posts = Post.objects.filter(user=user,is_draft=True).order_by('-created_at')
        reels = Reel.objects.filter(user=user,is_draft=True).order_by('-created_at')
        
        posts_serializer = PostSerializer(posts, many=True, context={'request': request}).data
        for item in posts_serializer:
            item['type'] = 'post'
        reels_serializer = ReelSerializer(reels, many=True, context={'request': request}).data
        for item in reels_serializer:
            item['type'] = 'reel'
        
        combined = posts_serializer + reels_serializer
        combined_sorted = sorted(combined, key=itemgetter('created_at'), reverse=True)


        if not combined_sorted:
            return Response({
                "success": True,
                "data": []
            }, status=status.HTTP_200_OK)
            
        return Response({
            "success": True,
            "data": combined_sorted
            ,
        },status.HTTP_200_OK)
        
