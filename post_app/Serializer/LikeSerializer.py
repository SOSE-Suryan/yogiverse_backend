from rest_framework import serializers
from post_app.models import Like, Comment

class LikeSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(source='user.id', read_only=True)
    user_name = serializers.CharField(source='user.username', read_only=True)
    full_name = serializers.SerializerMethodField(read_only=True)

    def get_full_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}" if obj.user.first_name and obj.user.last_name else obj.user.username
        
    class Meta:
        model = Like
        fields = ['id', 'content_type', 'object_id', 'created_at', 'user_id', 'user_name', 'full_name']
        read_only_fields = ['id', 'created_at', 'user_id', 'user_name', 'full_name']

