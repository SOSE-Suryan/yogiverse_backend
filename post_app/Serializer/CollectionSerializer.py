from rest_framework import serializers
from django.contrib.contenttypes.models import ContentType
from post_app.models import Post, Reel
from post_app.models import Collection, CollectionItem


class CollectionItemSerializer(serializers.ModelSerializer):
    content_type = serializers.CharField()

    class Meta:
        model = CollectionItem
        fields = ['id', 'collection', 'content_type', 'object_id', 'saved_at']

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


class CollectionSerializer(serializers.ModelSerializer):
    # collection_items = serializers.SerializerMethodField(read_only=True)

    # def get_collection_items(self, obj):
    #     items = CollectionItem.objects.filter(collection=obj).order_by('-saved_at')
    #     return CollectionItemSerializer(items, many=True).data
    
    class Meta:
        model = Collection
        fields = ['id', 'name', 'created_at'] #, 'collection_items']
