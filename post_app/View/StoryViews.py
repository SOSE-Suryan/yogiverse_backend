from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.exceptions import MethodNotAllowed
from post_app.models import Story, StoryView
from user_app.models import UserModel
from follower_app.models import Follower
from post_app.Serializer.StorySerializer import StorySerializer, StoryViewSerializer
from django.utils import timezone
from django.db.models import Q
from post_app.utils.mentions import save_mentions

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
        user_id = request.query_params.get('user_id')
        
        if user_id:
            try:
                user_obj = UserModel.objects.get(id=user_id)
            except UserModel.DoesNotExist:
                return Response({
                    "success": False,
                    "message": "User not found."
                }, status=status.HTTP_404_NOT_FOUND)
            stories = Story.objects.filter(user=user_obj, expires_at__gt=now).order_by('-created_at')
            serializer = self.get_serializer(stories, many=True)
            return Response({
                "success": True,
                "message": "stories retrieved",
                "data": serializer.data
            }, status=status.HTTP_200_OK)
        else:
        # Own stories
            user_stories = Story.objects.filter(user=user, expires_at__gt=now)
            # Others' stories
            # Get approved followings (users this user follows)
            following_users = UserModel.objects.filter(
                id__in=Follower.objects.filter(follower=user, status='approved').values_list('following_id', flat=True)
            )
            others = Story.objects.filter(user__in=following_users, expires_at__gt=now).exclude(user=user)

            # Separate viewed and unviewed
            viewed_story_ids = StoryView.objects.filter(viewer=user).values_list('story_id', flat=True)
            unviewed_stories = others.exclude(id__in=viewed_story_ids)
            viewed_stories = others.filter(id__in=viewed_story_ids)

            combined_queryset = list(user_stories) + list(unviewed_stories.order_by('-created_at')) + list(viewed_stories.order_by('-created_at'))
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
            story_instance = serializer.save(user=request.user)
            mentions = request.data.get('mentions', [])
            save_mentions(request.user, mentions, story_instance)
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
        story_instance = self.get_object()
        mentions = request.data.get('mentions', [])
        save_mentions(request.user, mentions, story_instance)
        serializer = self.get_serializer(story_instance)
        return Response({
            "success": True,
            "message": "Mentions updated successfully.",
            "data": serializer.data
        }, status=status.HTTP_200_OK)
        # raise MethodNotAllowed("PATCH", detail="Story update is not allowed.")

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



from rest_framework.views import APIView

class StoryViewCreateAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, story_id, *args, **kwargs):
        # story_id = request.data.get('story_id')
        # if not story_id:
        #     return Response({"success": False, "message": "story_id is required"}, status=400)

        try:
            story = Story.objects.get(id=story_id)
        except Story.DoesNotExist:
            return Response({"success": False, "message": "Story not found"}, status=404)

        if story.user == request.user:
            return Response({"success": True, "message": "It's your own story"}, status=200)

        view, created = StoryView.objects.get_or_create(story=story, viewer=request.user)

        return Response({
            "success": True,
            "message": "Story view recorded",
            "new_view": created
        }, status=200)



class StoryViewersListAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, story_id):
        try:
            story = Story.objects.get(id=story_id, user=request.user)
        except Story.DoesNotExist:
            return Response({"success": False, "message": "Story not found or permission denied"}, status=404)

        viewers = story.views.select_related('viewer').order_by('-viewed_at')
        serialized_data = StoryViewSerializer(viewers, many=True).data

        return Response({
            "success": True,
            "message": "Viewer list retrieved",
            "data": serialized_data
        }, status=200)
