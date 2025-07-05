from rest_framework import serializers
from django.contrib.contenttypes.models import ContentType
from post_app.models import Post, Reel
from post_app.models import Collection, CollectionItem
from post_app.Serializer.PostSerializer import PostSerializer
from post_app.Serializer.ReelSerializer import ReelSerializer

class CollectionItemSerializer(serializers.ModelSerializer):
    content_type = serializers.CharField()
    item_data = serializers.SerializerMethodField()

    class Meta:
        model = CollectionItem
        fields = ['id', 'collection', 'content_type', 'object_id', 'saved_at','is_collection','item_data']

    def validate(self, attrs):
        model_map = {'post': Post, 'reel': Reel}
        model_name = attrs['content_type'].lower()
        if model_name not in model_map:
            raise serializers.ValidationError({'content_type': 'Invalid content type'})
        ct = ContentType.objects.get_for_model(model_map[model_name])
        attrs['content_type'] = ct
        try:
            model_map[model_name].objects.get(id=attrs['object_id'])
        except model_map[model_name].DoesNotExist:
            raise serializers.ValidationError({'object_id': 'Object does not exist'})
        return attrs
    
    def create(self, validated_data):
        validated_data['is_collection'] = True  # Force set to True
        return super().create(validated_data)
    
    def get_item_data(self, obj):
        
        model_class = obj.content_type.model_class() 
        instance = model_class.objects.filter(id=obj.object_id).first()

        if not instance:
            return None

        if isinstance(instance, Post):
            return PostSerializer(instance).data
        elif isinstance(instance, Reel):
            return ReelSerializer(instance).data
        return None

    def create(self, validated_data):
        validated_data['is_collection'] = True  # Force set to TrueAdd commentMore actions
        return super().create(validated_data)
    
    def get_item_data(self, obj):
        
        model_class = obj.content_type.model_class() 
        instance = model_class.objects.filter(id=obj.object_id).first()

        if not instance:
            return None

        if isinstance(instance, Post):
            return PostSerializer(instance).data
        elif isinstance(instance, Reel):
            return ReelSerializer(instance).data
        return None

class CollectionSerializer(serializers.ModelSerializer):
    # collection_items = serializers.SerializerMethodField(read_only=True)

    # def get_collection_items(self, obj):
    #     items = CollectionItem.objects.filter(collection=obj).order_by('-saved_at')
    #     return CollectionItemSerializer(items, many=True).data
    
    class Meta:
        model = Collection
        fields = ['id', 'name', 'created_at'] #, 'collection_items']
