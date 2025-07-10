from rest_framework import viewsets, permissions
from post_app.models import Post, Reel, Story
from post_app.Serializer.PostSerializer import PostSerializer
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from post_app.Filters.PostFilter import PostsFilter
from post_app.Paginations.Paginations import MainPagination
from rest_framework import status


class IsOwnerOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        # Allow GET, HEAD, OPTIONS for everyone
        if request.method in permissions.SAFE_METHODS:
            return True
        # Allow write/delete only for the owner
        return obj.user == request.user


class PostViewSet(viewsets.ModelViewSet):
    serializer_class = PostSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = PostsFilter
    pagination_class = MainPagination    
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]

    def get_queryset(self):
        # Return all posts for retrieve/update/delete access checks
        return Post.objects.all().order_by('-created_at')

    def list(self, request, *args, **kwargs):
        self.serializer_class = PostSerializer
        queryset = self.filter_queryset(self.get_queryset().filter(user=request.user,is_draft=False))
        query_params = request.query_params.get('rows_per_page')
        self.paginator.page_size = int(query_params) if query_params else self.paginator.page_size
        # Pagination logic start
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True,context={'request': request})
            data = self.get_paginated_response(serializer.data)
            return Response({"success": True, "message": "records displayed", "data": data}, status=status.HTTP_200_OK)

        serializer = self.get_serializer(queryset, many=True)
        return Response({"success": True, "message": "records displayed", "data": serializer.data}, status=status.HTTP_200_OK)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()  # Now allows public access, permission check handled automatically
        serializer = self.get_serializer(instance)
        return Response({"success": True, "message": "record retrieved", "data": serializer.data}, status=status.HTTP_200_OK)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            self.perform_create(serializer)
            data = serializer.data
            return Response({"success": True, "message": "record created", "data": data}, status=status.HTTP_201_CREATED)
        else:
            errors = []
            for i in serializer.errors.values():
                errors.append(i[0])
            if len(errors) == 1:
                errors = errors[0]
            return Response({"success": False, "message": errors, "data": {}}, status=status.HTTP_400_BAD_REQUEST)
        
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