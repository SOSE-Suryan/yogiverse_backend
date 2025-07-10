from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from post_app.models import Reel
from post_app.Serializer.ReelSerializer import ReelSerializer
from post_app.Paginations.Paginations import MainPagination


class IsOwnerOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.user == request.user


class ReelViewSet(viewsets.ModelViewSet):
    serializer_class = ReelSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    pagination_class = MainPagination

    def get_queryset(self):
        # Needed for retrieve/edit/delete to work
        return Reel.objects.all().order_by('-created_at')

    def list(self, request, *args, **kwargs):
        # Return only the logged-in user's reels
        queryset = self.filter_queryset(self.get_queryset().filter(user=request.user,is_draft=False))
        rows = request.query_params.get('rows_per_page')
        self.paginator.page_size = int(rows) if rows else self.paginator.page_size

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            data = self.get_paginated_response(serializer.data)
            return Response({"success": True, "message": "records displayed", "data": data}, status=status.HTTP_200_OK)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response({"success": True, "message": "records displayed", "data": serializer.data}, status=status.HTTP_200_OK)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({"success": True, "message": "record retrieved", "data": serializer.data}, status=status.HTTP_200_OK)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            self.perform_create(serializer)
            return Response({"success": True, "message": "record created", "data": serializer.data}, status=status.HTTP_201_CREATED)

        errors = [v[0] for v in serializer.errors.values()]
        return Response({
            "success": False,
            "message": errors[0] if len(errors) == 1 else errors,
            "data": {}
        }, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response({"success": True, "message": "record deleted", "data": {}}, status=status.HTTP_200_OK)

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"success": True, "message": "record updated", "data": serializer.data}, status=status.HTTP_200_OK)
