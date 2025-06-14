from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.contrib.contenttypes.models import ContentType
from post_app.models import Like, Comment
from post_app.Serializer.CommentSerializer import CommentSerializer


class CommentCreateAPIView(generics.CreateAPIView):
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        return self.create_comment(request)

    def create_comment(self, request):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response({"success": True, "message": "Comment added", "data": serializer.data}, status=201)
        return Response({"success": False, "message": serializer.errors}, status=400)


class CommentUpdateAPIView(generics.UpdateAPIView):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated]

    def patch(self, request, *args, **kwargs):
        return self.update_comment(request, *args, **kwargs)

    def update_comment(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.user != request.user:
            return Response({"success": False, "message": "Permission denied"}, status=403)
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({"success": True, "message": "Comment updated", "data": serializer.data}, status=200)
        return Response({"success": False, "message": serializer.errors}, status=400)


class CommentDeleteAPIView(generics.DestroyAPIView):
    queryset = Comment.objects.all()
    permission_classes = [IsAuthenticated]

    def delete(self, request, *args, **kwargs):
        return self.delete_comment(request, *args, **kwargs)

    def delete_comment(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.user != request.user:
            return Response({"success": False, "message": "Permission denied"}, status=403)
        instance.delete()
        return Response({"success": True, "message": "Comment deleted"}, status=200)
