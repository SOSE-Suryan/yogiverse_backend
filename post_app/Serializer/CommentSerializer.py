from rest_framework import serializers
from post_app.models import Like, Comment
from django.contrib.contenttypes.models import ContentType


class CommentSerializer(serializers.ModelSerializer):
    content_type = serializers.CharField()
    user_id = serializers.IntegerField(source='user.id', read_only=True)
    user_name = serializers.CharField(source='user.username', read_only=True)
    full_name = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Comment
        fields = ['id', 'content_type', 'object_id', 'text', 'created_at', 'updated_at', 'user_id', 'user_name', 'full_name']
        read_only_fields = ['id', 'created_at', 'updated_at', 'user_id', 'user_name', 'full_name']

    def get_full_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}" if obj.user.first_name and obj.user.last_name else obj.user.username
    
    def validate_content_type(self, value):
        try:
            return ContentType.objects.get(model=value.lower())
        except ContentType.DoesNotExist:
            raise serializers.ValidationError("Invalid content type")

    def create(self, validated_data):
        content_type = validated_data.pop('content_type')
        return Comment.objects.create(content_type=content_type, **validated_data)