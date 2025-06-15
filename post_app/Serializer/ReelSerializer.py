from rest_framework import serializers
from post_app.models import Post, PostMedia, Reel, Story


class ReelSerializer(serializers.ModelSerializer):
    like_count = serializers.SerializerMethodField(read_only=True)
    comment_count = serializers.SerializerMethodField(read_only=True)
    type = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Reel
        fields = [
            'id', 'user', 'caption', 'video_file', 'duration', 'is_draft',
            'allow_comments', 'hide_like_count', 'music_track', 'created_at', 'updated_at',
            'like_count', 'comment_count', 'type'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']

    def get_like_count(self, obj):
        return obj.likes.count()
    
    def get_comment_count(self, obj):
        return obj.comments.count()
    
    def get_type(self, obj):
        return 'reel'
    
    def create(self, validated_data):
        validated_data.pop('tags', [])
        validated_data['user'] = self.context['request'].user
        return Reel.objects.create(**validated_data)

    def update(self, instance, validated_data):
        validated_data.pop('tags', [])
        video_file = validated_data.get('video_file', None)
        if video_file:
            instance.video_file.delete(save=False)  # delete old video if needed
            instance.video_file = video_file

        for attr, value in validated_data.items():
            if attr != 'video_file':
                setattr(instance, attr, value)

        instance.save()
        return instance
    