from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from post_app.models import Reel
from post_app.Serializer.ReelSerializer import ReelSerializer
from ..permissions import IsOwnerOrReadOnly
from django_filters.rest_framework import DjangoFilterBackend
from post_app.Paginations.Paginations import MainPagination

class ReelViewSet(viewsets.ModelViewSet):
    serializer_class = ReelSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    pagination_class = MainPagination

    def get_queryset(self):
        return Reel.objects.filter(user=self.request.user).order_by('-created_at')

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        query_params = request.query_params.get('rows_per_page')
        self.paginator.page_size = int(query_params) if query_params else self.paginator.page_size
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return Response({"success": True, "message": "records displayed", "data": self.get_paginated_response(serializer.data)}, status=status.HTTP_200_OK)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response({"success": True, "message": "records displayed", "data": serializer.data}, status=status.HTTP_200_OK)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.user != request.user:
            return Response({'status': False, 'detail': 'You do not have permission to access this object.'}, status=status.HTTP_403_FORBIDDEN)
        
        serializer = self.get_serializer(instance)
        return Response({"success": True, "message": "record retrieved", "data": serializer.data}, status=status.HTTP_200_OK)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            self.perform_create(serializer)
            return Response({"success": True, "message": "record created", "data": serializer.data}, status=status.HTTP_201_CREATED)
        else:
            errors = []
            for i in serializer.errors.values():
                errors.append(i[0])
            if len(errors) == 1:
                errors = errors[0]
            return Response({"success": False, "message": errors, "data": {}}, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return Response({"success": True, "message": "record deleted", "data": {}}, status=status.HTTP_200_OK)

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"success": True, "message": "record updated", "data": serializer.data}, status=status.HTTP_200_OK)
