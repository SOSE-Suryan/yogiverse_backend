from rest_framework import viewsets, permissions
from post_app.models import Post, Reel, Story
from post_app.Serializer.PostSerializer import PostSerializer
from ..permissions import IsOwnerOrReadOnly
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from post_app.Filters.PostFilter import PostsFilter
from post_app.Paginations.Paginations import MainPagination
from rest_framework import status


class PostViewSet(viewsets.ModelViewSet):
    serializer_class = PostSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = PostsFilter
    pagination_class = MainPagination    
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]

    def get_queryset(self):
        return Post.objects.filter(user=self.request.user).order_by('-created_at')

    def list(self, request, *args, **kwargs):
        self.serializer_class = PostSerializer
        queryset = self.filter_queryset(self.get_queryset().filter(user=request.user))
        query_params = request.query_params.get('rows_per_page')
        self.paginator.page_size = int(query_params) if query_params else self.paginator.page_size
        # Pagination logic start
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            data = serializer.data
            return Response({"success": True, "message": "records displayed", "data": data}, status.HTTP_200_OK)
        # Pagination logic end
        serializer = self.get_serializer(queryset, many=True)
        data = serializer.data
        return Response({"success": True, "message": "records displayed", "data": data}, status.HTTP_200_OK)


    def retrieve(self, request, *args, **kwargs):
        self.serializer_class = PostSerializer
        queryset = self.get_object()
        if queryset.user != request.user:
            return Response({'status': False, 'detail': 'You do not have permission to access this object.'}, status=status.HTTP_403_FORBIDDEN)
        serializer = self.get_serializer(queryset)
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
        queryset = self.get_object()
        queryset.delete()
        return Response({"success": True, "message": "record deleted", "data": {}}, status=status.HTTP_200_OK)
    
    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(
            instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"success": True, "message": "record updated", "data": serializer.data}, status=status.HTTP_200_OK)