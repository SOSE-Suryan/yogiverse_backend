from rest_framework import serializers
from post_app.models import Story
from datetime import timedelta
from django.utils import timezone


class StorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Story
        fields = [
            'id', 'user', 'media_file', 'caption', 'expires_at',
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
