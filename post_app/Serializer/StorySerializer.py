from rest_framework import serializers
from post_app.models import Story, StoryView
from datetime import timedelta
from django.utils import timezone
from user_app.models import ProfileModel
from user_app.Serializer.UserSerializer import ProfileSerializer 

class StorySerializer(serializers.ModelSerializer):
    profile = serializers.SerializerMethodField(read_only=True)
    is_seen = serializers.SerializerMethodField()
    is_video = serializers.SerializerMethodField()
    mentions = serializers.ListField(child=serializers.IntegerField(), required=False, write_only=True)
    mentioned_users = serializers.SerializerMethodField(read_only=True)
    is_mention = serializers.SerializerMethodField(read_only=True)

    def get_profile(self, obj):
        try:
            profile = obj.user.profile 
            return ProfileSerializer(profile).data
        except ProfileModel.DoesNotExist:
            return None
        
    def get_mentioned_users(self, obj):
        from post_app.models import MentionModel
        from django.contrib.contenttypes.models import ContentType

        # current_user = self.context['request'].user
        request = self.context.get('request', None)
        current_user = getattr(request, 'user', None)
        from chat_app.models import ChatModel  # Use your actual ChatModel

        ctype = ContentType.objects.get_for_model(obj)
        mentions = MentionModel.objects.filter(content_type=ctype, object_id=obj.id)
        
        
        result = []   
        for m in mentions: 
            mentioned_user = m.mentioned_user
            # Find a single chat (DM) between current_user and mentioned_user
            chat_id = None
            if current_user and current_user.is_authenticated and current_user != mentioned_user:
                chat = ChatModel.objects.filter(
                    members=current_user).filter(members=mentioned_user).filter(is_single_chat=True).first()
                if chat:
                    chat_id = str(chat.chat_id)
            result.append({
                "id": mentioned_user.id,
                "username": mentioned_user.username,
                "slug": obj.slug,
                "chat_id": chat_id,
            })
        return result
    
    def get_is_mention(self, obj):
        request = self.context.get("request", None)
        if not request or not hasattr(request, "user") or not request.user or not request.user.is_authenticated:
            return False
        from post_app.models import MentionModel
        from django.contrib.contenttypes.models import ContentType
        ctype = ContentType.objects.get_for_model(obj)
        
        mentions = MentionModel.objects.filter(content_type=ctype, object_id=obj.id,mentioned_user = request.user).exists()
        return mentions
    class Meta:
        model = Story
        fields = [
            'id', 'user', 'profile','media_file', 'caption', 'expires_at',
            'is_highlighted', 'created_at', 'updated_at', 'is_seen', 'is_video','mentions','mentioned_users','is_mention','mention_user_data'
        ]
        read_only_fields = ['id', 'user', 'expires_at', 'created_at', 'updated_at']

    # OPTIONAL: If expires_at is still being validated as required, add this:
    extra_kwargs = {
        'expires_at': {'required': False}
    }

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        mentions = validated_data.pop('mentions', None)
        validated_data['expires_at'] = timezone.now() + timedelta(hours=24)
        return Story.objects.create(**validated_data)

    def get_is_seen(self, obj):
        user = self.context['request'].user
        return StoryView.objects.filter(story=obj, viewer=user).exists()

    def get_is_video(self, obj):
        media_file = obj.media_file.name.lower()
        return media_file.endswith('.mp4') or media_file.endswith('.mov') or media_file.endswith('.avi')


class StoryViewSerializer(serializers.ModelSerializer):
    viewer_profile_data = serializers.SerializerMethodField()

    def get_viewer_profile_data(self, obj):
        try:
            profile = obj.viewer.profile
            return ProfileSerializer(profile).data
        except ProfileModel.DoesNotExist:
            return None
        
    class Meta:
        model = StoryView
        fields = "__all__"
        read_only_fields = ['viewed_at']
