from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from post_app.models import RecentSearch
from post_app.Serializer.RecentSearchSerializer import RecentSearchSerializer
from rest_framework.views import APIView


class RecentSearchCreateAPIView(generics.CreateAPIView):
    serializer_class = RecentSearchSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        user = self.request.user

        # Enforce a max of 5 recent searches
        existing = RecentSearch.objects.filter(user=user).order_by('-searched_at')

        # Optional: prevent duplicates of same object_id or query
        new_query = serializer.validated_data.get('query')
        new_ct = serializer.validated_data.get('content_type')
        new_obj_id = serializer.validated_data.get('object_id')

        for search in existing:
            if (
                (new_query and search.query == new_query)
                or (new_ct and new_obj_id and search.content_type == new_ct and search.object_id == new_obj_id)
            ):
                search.delete()
                break

        if existing.count() >= 5:
            # delete oldest search
            existing.last().delete()

        serializer.save(user=user)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            self.perform_create(serializer)
            return Response({"success": True, "message": "Search recorded", "data": serializer.data}, status=201)
        return Response({"success": False, "message": serializer.errors}, status=400)


class RecentSearchListAPIView(generics.ListAPIView):
    serializer_class = RecentSearchSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return RecentSearch.objects.filter(user=self.request.user).order_by('-searched_at')

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            "success": True,
            "message": "Recent search history retrieved",
            "data": serializer.data
        }, status=200)


class RecentSearchDeleteAPIView(generics.DestroyAPIView):
    permission_classes = [IsAuthenticated]
    queryset = RecentSearch.objects.all()
    lookup_field = 'pk'

    def delete(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.user != request.user:
            return Response({"success": False, "message": "Unauthorized access."}, status=403)
        instance.delete()
        return Response({"success": True, "message": "Search history entry deleted."}, status=200)


class ClearAllRecentSearchesAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request):
        deleted_count, _ = RecentSearch.objects.filter(user=request.user).delete()
        return Response({
            "success": True,
            "message": f"All recent search history deleted ({deleted_count} items)."
        }, status=200)
