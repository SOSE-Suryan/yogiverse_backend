from rest_framework import serializers
from post_app.models import Like, Comment
from django.contrib.contenttypes.models import ContentType


class CommentSerializer(serializers.ModelSerializer):
    content_type = serializers.CharField()

    class Meta:
        model = Comment
        fields = ['id', 'content_type', 'object_id', 'text', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate_content_type(self, value):
        try:
            return ContentType.objects.get(model=value.lower())
        except ContentType.DoesNotExist:
            raise serializers.ValidationError("Invalid content type")

    def create(self, validated_data):
        content_type = validated_data.pop('content_type')
        return Comment.objects.create(content_type=content_type, **validated_data)