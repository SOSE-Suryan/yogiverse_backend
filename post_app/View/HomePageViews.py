from django.contrib.auth import get_user_model
from django.db.models import Q
from itertools import chain
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from follower_app.models import Follower
from post_app.models import Post, Reel
from post_app.Paginations.Paginations import MainPagination
from post_app.Serializer.ReelSerializer import CombinedFeedSerializer

User = get_user_model()

class CombinedFeedAPIView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    pagination_class = MainPagination

    def get(self, request, *args, **kwargs):
        user = request.user

        # Step 1: Get following users
        following_user_ids = Follower.objects.filter(follower=user).values_list('following_id', flat=True)

        target_user_ids = []
        if following_user_ids.exists():
            target_user_ids.extend(following_user_ids)

        follower_user_ids = Follower.objects.filter(following=user).values_list('follower_id', flat=True)
        if follower_user_ids.exists():
            target_user_ids.extend(follower_user_ids)

        vendor_user_ids = User.objects.filter(role='vendor').values_list('id', flat=True)
        target_user_ids.extend(vendor_user_ids)

        # Remove duplicates but preserve order
        target_user_ids = list(dict.fromkeys(target_user_ids))

        # Step 4: Fetch Posts and Reels from those users
        posts = Post.objects.filter(user_id__in=target_user_ids).order_by('-created_at')
        reels = Reel.objects.filter(user_id__in=target_user_ids).order_by('-created_at')

        # Step 5: Combine and sort
        combined_items = sorted(chain(posts, reels), key=lambda x: x.created_at, reverse=True)
        
        # Step 6: Manual pagination (because it's not a queryset)
        page = self.paginate_queryset(combined_items)
        if page is not None:
            serializer = CombinedFeedSerializer(page, many=True)
            data = self.get_paginated_response(serializer.data)
            return Response({"success": True, "message": "records displayed", "data": data}, status.HTTP_200_OK)

        serializer = CombinedFeedSerializer(combined_items, many=True)
        return Response({"success": True, "data": serializer.data})
