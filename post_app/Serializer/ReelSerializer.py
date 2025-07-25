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
    mentions = serializers.ListField(child=serializers.IntegerField(), required=False, write_only=True)
    mentioned_users = serializers.SerializerMethodField(read_only=True)
    is_mention = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Reel
        fields = [
            'id', 'user', 'profile','caption', 'video_file', 'duration', 'is_draft',
            'allow_comments', 'hide_like_count', 'music_track', 'created_at', 'updated_at',
            'like_count', 'comment_count', 'type','mentions','mentioned_users','is_mention'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']
        
    
    def get_mentioned_users(self, obj):
        from post_app.models import MentionModel
        from django.contrib.contenttypes.models import ContentType

        # current_user = self.context['request'].user
        request = self.context.get('request', None)
        current_user = getattr(request, 'user', None)
        from chat_app.models import ChatModel  # Use your actual ChatModel

        ctype = ContentType.objects.get_for_model(obj)
        mentions = MentionModel.objects.filter(content_type=ctype, object_id=obj.id)
        
        
        result = []   
        for m in mentions: 
            mentioned_user = m.mentioned_user
            # Find a single chat (DM) between current_user and mentioned_user
            chat_id = None
            if current_user and current_user.is_authenticated and current_user != mentioned_user:
                chat = ChatModel.objects.filter(
                    members=current_user).filter(members=mentioned_user).filter(is_single_chat=True).first()
                if chat:
                    chat_id = str(chat.chat_id)
            result.append({
                "id": mentioned_user.id,
                "username": mentioned_user.username,
                "slug": obj.slug,
                "chat_id": chat_id,
            })
        return result
    
    # def get_mentioned_users(self, obj):
    #     from post_app.models import MentionModel
    #     from django.contrib.contenttypes.models import ContentType
    #     ctype = ContentType.objects.get_for_model(obj)
    #     mentions = MentionModel.objects.filter(content_type=ctype, object_id=obj.id)
    #     return [
    #     {"id": m.mentioned_user.id, "username": m.mentioned_user.username,"slug":obj.slug}
    #     for m in mentions
    # ]

    def get_is_mention(self, obj):
        request = self.context.get("request", None)
        if not request or not hasattr(request, "user") or not request.user or not request.user.is_authenticated:
            return False
        from post_app.models import MentionModel
        from django.contrib.contenttypes.models import ContentType
        ctype = ContentType.objects.get_for_model(obj)
        
        mentions = MentionModel.objects.filter(content_type=ctype, object_id=obj.id,mentioned_user = request.user).exists()
        return mentions 
    
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
        validated_data.pop('mentions', [])
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
    
    is_collection = serializers.SerializerMethodField()
    collection_id = serializers.SerializerMethodField()

    def _get_collection_item(self, obj):
        """Private method to get CollectionItem instance once per object."""
        if hasattr(obj, '_collection_item'):
            return obj._collection_item

        request = self.context.get('request')
        user = getattr(request, 'user', None)
        
        if not user or not user.is_authenticated:
            obj._collection_item = None
            return None

        content_type = ContentType.objects.get_for_model(obj._meta.model)
        item = CollectionItem.objects.filter(
            content_type=content_type,
            object_id=obj.id,
            is_collection=True,
            collection__user=user  # if collection is user-specific
        ).first()

        obj._collection_item = item
        return item

    def get_is_collection(self, obj):
        return bool(self._get_collection_item(obj))

    def get_collection_id(self, obj):
        collection_item = self._get_collection_item(obj)
        return collection_item.collection.id if collection_item else None
    
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
