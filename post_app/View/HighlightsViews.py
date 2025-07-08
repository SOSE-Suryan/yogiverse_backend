from rest_framework import viewsets, permissions,status
from post_app.models import HighlightModel
from post_app.Serializer.HighlightSerializer import HighlightSerializer
from rest_framework.response import Response
from rest_framework.decorators import action 

class HighlightViewSet(viewsets.ModelViewSet):
    serializer_class = HighlightSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Show highlights of the authenticated user
        return HighlightModel.objects.filter(user=self.request.user).order_by('-created_at')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['post'], url_path='remove-story')
    def remove_story(self, request, pk=None):
        highlight = self.get_object()
        story_id = request.data.get('story_id')
        if not story_id:
            return Response({"detail": "story_id is required."}, status=400)
        story = highlight.stories.filter(id=story_id).first()
        if not story:
            return Response({"detail": "Story not found in this highlight."}, status=404)
        highlight.stories.remove(story)
        if not story.in_highlights.exists():
            story.is_highlighted = False
            story.save(update_fields=['is_highlighted'])
        return Response({"success": True, "message": "Story removed from highlight."})
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        # Optionally, un-highlight all stories that are not in any other highlight
        for story in instance.stories.all():
            if story.in_highlights.count() == 1:  # Only in this highlight
                story.is_highlighted = False
                story.save(update_fields=['is_highlighted'])
        self.perform_destroy(instance)
        return Response({
            "success": True,
            "message": "highlight deleted",
            "data": {}
        }, status=status.HTTP_200_OK)