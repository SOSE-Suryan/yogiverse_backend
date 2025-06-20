from rest_framework import serializers
from post_app.models import Story
from datetime import timedelta
from django.utils import timezone
from user_app.models import ProfileModel
from user_app.Serializer.UserSerializer import ProfileSerializer 

class StorySerializer(serializers.ModelSerializer):
    profile = serializers.SerializerMethodField(read_only=True)

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
            'is_highlighted', 'created_at', 'updated_at'
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
