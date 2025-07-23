from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from post_app.models import MentionModel, Post, Reel
from post_app.Serializer.PostSerializer import PostSerializer
from post_app.Serializer.ReelSerializer import ReelSerializer
from user_app.models import UserModel
from django.contrib.contenttypes.models import ContentType

class MentionedAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        
        user_id = request.query_params.get('user_id')
        if user_id:
            try:
                user = UserModel.objects.get(id=user_id)
            except UserModel.DoesNotExist:
                return Response({
                    "success": False,
                    "message": "User not found."
                }, status=status.HTTP_404_NOT_FOUND)
        else:
            user = request.user


        mentions = MentionModel.objects.filter(mentioned_user=user).select_related('content_type')
        tagged_items = []
        for mention in mentions:
            obj = mention.content_object
            
            current_user_is_mentioned = MentionModel.objects.filter(
                mentioned_user=request.user,
                content_type=mention.content_type,
                object_id=mention.object_id
            ).exists()
            
            if isinstance(obj, Post):
                data = PostSerializer(obj, context={'request': request}).data
                data['type'] = 'post'
                data['is_mention'] = current_user_is_mentioned
                tagged_items.append(data)
            elif isinstance(obj, Reel):
                data = ReelSerializer(obj, context={'request': request}).data
                data['type'] = 'reel'
                data['is_mention'] = current_user_is_mentioned
                tagged_items.append(data)
            # elif ... for stories if needed

        # Sort by created_at (newest first)
        tagged_items_sorted = sorted(tagged_items, key=lambda x: x.get('created_at', ''), reverse=True)

        return Response({
            "success": True,
            "data": tagged_items_sorted
        }, status=status.HTTP_200_OK)


    def delete(self, request):
        object_id = request.data.get('object_id')
        content_type_str = request.data.get('content_type')
        user_id = request.data.get('user_id')

        if not all([object_id, content_type_str, user_id]):
            return Response({"success": False, "message": "Missing required fields."}, status=400)

        # Get content type
        try:
            content_type = ContentType.objects.get(model=content_type_str)
        except ContentType.DoesNotExist:
            return Response({"success": False, "message": "Invalid content type."}, status=400)

        try:
            mention = MentionModel.objects.get(
                content_type=content_type,
                object_id=object_id,
                mentioned_user_id=user_id
            )
        except MentionModel.DoesNotExist:
            return Response({"success": False, "message": "Mention does not exist."}, status=404)

        # Authority check: only creator or mentioned user
        if request.user != mention.creator and request.user.id != int(user_id):
            return Response({"success": False, "message": "Not authorized."}, status=403)

        mention.delete()
        return Response({"success": True, "message": "Mention removed successfully."}, status=200)
