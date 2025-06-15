from rest_framework import serializers
from post_app.models import Post, PostMedia, Reel, Story, Tag
from django.utils.text import slugify
import re

class PostMediaSerializer(serializers.ModelSerializer):
    class Meta:
        model = PostMedia
        fields = ['id', 'media_file', 'is_video']

class PostSerializer(serializers.ModelSerializer):
    media = PostMediaSerializer(many=True, required=False)
    like_count = serializers.SerializerMethodField(read_only=True)
    comment_count = serializers.SerializerMethodField(read_only=True)
    type = serializers.SerializerMethodField(read_only=True)
    tags = serializers.SlugRelatedField(
        many=True,
        queryset=Tag.objects.all(),
        slug_field='name'
    )

    class Meta:
        model = Post
        fields = [
            'id', 'user', 'caption', 'is_draft', 'allow_comments', 'hide_like_count',
            'location', 'media', 'created_at', 'updated_at',
            'like_count', 'comment_count', 'type', 'tags'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']

    def get_like_count(self, obj):
        return obj.likes.count()

    def get_comment_count(self, obj):
        return obj.comments.count()

    def get_type(self, obj):
        return 'post'

    def handle_tags(self, post, caption):
        tags = re.findall(r'#(\w+)', caption or "")
        tag_objs = []
        for name in tags:
            tag, _ = Tag.objects.get_or_create(name=name, defaults={'slug': slugify(name)})
            tag_objs.append(tag)
        post.tags.set(tag_objs)
    
    def create(self, validated_data):
        request = self.context['request']
        user = request.user

        # Remove media if present in validated_data
        validated_data.pop('media', None)
        validated_data.pop('tags', [])

        post = Post.objects.create(user=user, **validated_data)

        media_files = request.FILES.getlist('media_files')
        media_metadata_json = request.data.get('media_metadata')

        if media_metadata_json:
            import json
            try:
                media_metadata = json.loads(media_metadata_json)
            except json.JSONDecodeError:
                raise serializers.ValidationError({'media_metadata': 'Invalid JSON format.'})

            if len(media_metadata) != len(media_files):
                raise serializers.ValidationError({'media_files': 'Number of files and metadata must match.'})

            for i, media_file in enumerate(media_files):
                PostMedia.objects.create(
                    post=post,
                    media_file=media_file,
                    is_video=media_metadata[i].get('is_video', False)
                )
        
        self.handle_tags(post, validated_data.get('caption'))

        return post

    def update(self, instance, validated_data):
        request = self.context['request']

        # Remove media if passed through validated_data
        validated_data.pop('media', None)
        validated_data.pop('tags', [])

        # Update basic fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Handle new media uploads
        media_files = request.FILES.getlist('media_files')
        media_metadata_json = request.data.get('media_metadata')

        if media_files and media_metadata_json:
            import json
            try:
                media_metadata = json.loads(media_metadata_json)
            except json.JSONDecodeError:
                raise serializers.ValidationError({'media_metadata': 'Invalid JSON format.'})

            if len(media_metadata) != len(media_files):
                raise serializers.ValidationError({'media_files': 'Number of files and metadata must match.'})

            # Clear old media before adding new ones
            instance.media.all().delete()

            for i, media_file in enumerate(media_files):
                PostMedia.objects.create(
                    post=instance,
                    media_file=media_file,
                    is_video=media_metadata[i].get('is_video', False)
                )

        # Re-handle tags only if caption was updated
        if 'caption' in validated_data:
            self.handle_tags(instance, validated_data.get('caption'))

        return instance
