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

    def get_profile(self, obj):
        try:
            profile = obj.user.profile 
            return ProfileSerializer(profile).data
        except ProfileModel.DoesNotExist:
            return None
        
    class Meta:
        model = Story
        fields = [
            'id', 'user', 'profile','media_file', 'caption', 'expires_at',
            'is_highlighted', 'created_at', 'updated_at', 'is_seen', 'is_video'
        ]
        read_only_fields = ['id', 'user', 'expires_at', 'created_at', 'updated_at']

    # OPTIONAL: If expires_at is still being validated as required, add this:
    extra_kwargs = {
        'expires_at': {'required': False}
    }

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
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
