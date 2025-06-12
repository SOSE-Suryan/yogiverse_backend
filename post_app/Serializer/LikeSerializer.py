from rest_framework import serializers
from post_app.models import Like, Comment

class LikeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Like
        fields = ['id', 'content_type', 'object_id', 'created_at']
        read_only_fields = ['id', 'created_at']

