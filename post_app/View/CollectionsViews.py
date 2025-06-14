from rest_framework import generics, permissions, status
from rest_framework.response import Response
from post_app.models import Collection, CollectionItem
from post_app.Serializer.CollectionSerializer import CollectionSerializer, CollectionItemSerializer
from django.contrib.contenttypes.models import ContentType
from django.db import IntegrityError
from post_app.Paginations.Paginations import MainPagination


class CollectionListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = CollectionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Collection.objects.filter(user=self.request.user)

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            "success": True,
            "message": "Collections fetched successfully",
            "data": serializer.data
        }, status=status.HTTP_200_OK)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response({
                "success": True,
                "message": "Collection created successfully",
                "data": serializer.data
            }, status=status.HTTP_201_CREATED)
        return Response({
            "success": False,
            "message": serializer.errors,
            "data": {}
        }, status=status.HTTP_400_BAD_REQUEST)


class CollectionDetailAPIView(generics.RetrieveAPIView):
    queryset = Collection.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = CollectionSerializer
    pagination_class = MainPagination

    def get(self, request, *args, **kwargs):
        collection = self.get_object()

        if collection.user != request.user:
            return Response({"success": False, "message": "Permission denied"}, status=403)

        # Serialize basic collection info
        collection_data = self.get_serializer(collection).data

        # Paginate collection items
        items_qs = CollectionItem.objects.filter(collection=collection).order_by('-saved_at')
        query_params = request.query_params.get('rows_per_page')
        self.paginator.page_size = int(query_params) if query_params else self.paginator.page_size

        # Pagination logic start
        page = self.paginate_queryset(items_qs)
        if page is not None:
            serializer = CollectionItemSerializer(page, many=True)
            data = self.get_paginated_response(serializer.data)
            return Response({"success": True, "message": "records displayed", "collection": collection_data, "data": data}, status.HTTP_200_OK)
        # Pagination logic end

        items_data = CollectionItemSerializer(items_qs, many=True).data

        return Response({
            "success": True,
            "message": "Collection fetched successfully",
            "data": {
                "collection": collection_data,
                "items": items_data
            }
        })


class AddToCollectionAPIView(generics.CreateAPIView):
    serializer_class = CollectionItemSerializer
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            try:
                serializer.save()
                return Response({
                    "success": True,
                    "message": "Item saved to collection",
                    "data": serializer.data
                }, status=status.HTTP_201_CREATED)
            except IntegrityError:
                return Response({
                    "success": False,
                    "message": "Item already exists in this collection",
                    "data": {}
                }, status=status.HTTP_400_BAD_REQUEST)
        return Response({
            "success": False,
            "message": serializer.errors,
            "data": {}
        }, status=status.HTTP_400_BAD_REQUEST)

class RemoveFromCollectionAPIView(generics.DestroyAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, *args, **kwargs):
        collection_id = kwargs.get('collection_id')
        object_id = kwargs.get('object_id')
        content_type = kwargs.get('content_type')

        from post_app.models import Post, Reel
        model_map = {'post': Post, 'reel': Reel}
        model = model_map.get(content_type)
        if not model:
            return Response({"success": False, "message": "Invalid content type"}, status=400)

        try:
            ct = ContentType.objects.get_for_model(model)
            item = CollectionItem.objects.get(collection_id=collection_id, content_type=ct, object_id=object_id)
            item.delete()
            return Response({"success": True, "message": "Item removed from collection"}, status=200)
        except CollectionItem.DoesNotExist:
            return Response({"success": False, "message": "Item not found in collection"}, status=404)

class DeleteCollectionAPIView(generics.DestroyAPIView):
    queryset = Collection.objects.all()
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, *args, **kwargs):
        collection = self.get_object()
        if collection.user != request.user:
            return Response({"success": False, "message": "Permission denied"}, status=403)
        collection.delete()
        return Response({"success": True, "message": "Collection deleted"}, status=200)
