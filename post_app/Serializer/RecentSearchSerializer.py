from rest_framework import serializers
from django.contrib.contenttypes.models import ContentType
from post_app.models import RecentSearch

class RecentSearchSerializer(serializers.ModelSerializer):
    class Meta:
        model = RecentSearch
        fields = ['id', 'query', 'content_type', 'object_id', 'searched_at']
        read_only_fields = ['id', 'searched_at']

    def validate(self, data):
        content_type = data.get("content_type")
        object_id = data.get("object_id")

        if not data.get("query") and (not content_type or not object_id):
            raise serializers.ValidationError("Either 'query' or 'content_type' and 'object_id' must be provided.")
        return data
