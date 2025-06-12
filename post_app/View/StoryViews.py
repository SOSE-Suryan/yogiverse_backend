from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.exceptions import MethodNotAllowed
from post_app.models import Story
from post_app.Serializer.StorySerializer import StorySerializer
from ..permissions import IsOwnerOrReadOnly

class StoryViewSet(viewsets.ModelViewSet):
    serializer_class = StorySerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]

    def get_queryset(self):
        return Story.objects.filter(user=self.request.user).order_by('-created_at')

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            "success": True,
            "message": "stories retrieved",
            "data": serializer.data
        }, status=status.HTTP_200_OK)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.user != request.user:
            return Response(
                {"success": False, "message": "You do not have permission to access this story.", "data": {}},
                status=status.HTTP_403_FORBIDDEN
            )
        serializer = self.get_serializer(instance)
        return Response({"success": True, "message": "story retrieved", "data": serializer.data}, status=status.HTTP_200_OK)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response({"success": True, "message": "story created", "data": serializer.data}, status=status.HTTP_201_CREATED)
        else:
            errors = [e[0] for e in serializer.errors.values()]
            return Response({"success": False, "message": errors[0] if len(errors) == 1 else errors, "data": {}}, status=status.HTTP_400_BAD_REQUEST)

    def partial_update(self, request, *args, **kwargs):
        raise MethodNotAllowed("PATCH", detail="Story update is not allowed.")

    def update(self, request, *args, **kwargs):
        raise MethodNotAllowed("PUT", detail="Story update is not allowed.")

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return Response({"success": True, "message": "story deleted", "data": {}}, status=status.HTTP_200_OK)
