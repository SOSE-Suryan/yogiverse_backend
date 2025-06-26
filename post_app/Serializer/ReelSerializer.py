from rest_framework import serializers
from post_app.models import Post, PostMedia, Reel, Story,CollectionItem,ContentType,Like
from post_app.Serializer.PostSerializer import PostSerializer
from user_app.models import ProfileModel
from user_app.Serializer.UserSerializer import ProfileSerializer 

class ReelSerializer(serializers.ModelSerializer):
    like_count = serializers.SerializerMethodField(read_only=True)
    comment_count = serializers.SerializerMethodField(read_only=True)
    type = serializers.SerializerMethodField(read_only=True)
    profile = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Reel
        fields = [
            'id', 'user', 'profile','caption', 'video_file', 'duration', 'is_draft',
            'allow_comments', 'hide_like_count', 'music_track', 'created_at', 'updated_at',
            'like_count', 'comment_count', 'type'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']
        
    def get_profile(self, obj):
        try:
            profile = obj.user.profile 
            return ProfileSerializer(profile).data
        except ProfileModel.DoesNotExist:
            return None

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
    
    
class CombinedFeedSerializer(serializers.Serializer):
    type = serializers.SerializerMethodField()
    data = serializers.SerializerMethodField()
    profile = serializers.SerializerMethodField()
    is_like = serializers.SerializerMethodField()
    
    def get_is_like(self, obj):

        request = self.context.get('request')         
        user = getattr(request, 'user', None)

        if not user or not user.is_authenticated:
            return False

        content_type = ContentType.objects.get_for_model(obj._meta.model)

        is_like= Like.objects.filter(
            user=user,
            content_type=content_type,
            object_id=obj.id,
            is_like=True
        ).exists()
        
        return is_like
    
    def get_type(self, obj):
        return 'post' if isinstance(obj, Post) else 'reel'

    def get_data(self, obj):
        if isinstance(obj, Post):
            return PostSerializer(obj).data
        return ReelSerializer(obj).data

    def get_profile(self, obj):
        if isinstance(obj, Post):
            return ProfileSerializer(obj.user.profile).data
        return ProfileSerializer(obj.user.profile).data
