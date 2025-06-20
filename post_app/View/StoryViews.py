from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.exceptions import MethodNotAllowed
from post_app.models import Story
from post_app.Serializer.StorySerializer import StorySerializer
from django.utils import timezone
from django.db.models import Q


class IsOwnerOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.user == request.user
    

class StoryViewSet(viewsets.ModelViewSet):
    serializer_class = StorySerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]

    def get_queryset(self):
        # Return all unexpired stories (used for retrieve/delete permissions)
        return Story.objects.filter(expires_at__gt=timezone.now()).order_by('-created_at')

    def list(self, request, *args, **kwargs):
        now = timezone.now()
        user = request.user

        # Own stories
        user_stories = Story.objects.filter(user=user, expires_at__gt=now)
        # Others' stories
        other_stories = Story.objects.filter(~Q(user=user), expires_at__gt=now)

        combined_queryset = list(user_stories) + list(other_stories)
        serializer = self.get_serializer(combined_queryset, many=True)

        return Response({
            "success": True,
            "message": "stories retrieved",
            "data": serializer.data
        }, status=status.HTTP_200_OK)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()  # Permission checked by IsOwnerOrReadOnly
        serializer = self.get_serializer(instance)
        return Response({
            "success": True,
            "message": "story retrieved",
            "data": serializer.data
        }, status=status.HTTP_200_OK)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response({
                "success": True,
                "message": "story created",
                "data": serializer.data
            }, status=status.HTTP_201_CREATED)

        errors = [e[0] for e in serializer.errors.values()]
        return Response({
            "success": False,
            "message": errors[0] if len(errors) == 1 else errors,
            "data": {}
        }, status=status.HTTP_400_BAD_REQUEST)

    def partial_update(self, request, *args, **kwargs):
        raise MethodNotAllowed("PATCH", detail="Story update is not allowed.")

    def update(self, request, *args, **kwargs):
        raise MethodNotAllowed("PUT", detail="Story update is not allowed.")

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response({
            "success": True,
            "message": "story deleted",
            "data": {}
        }, status=status.HTTP_200_OK)
