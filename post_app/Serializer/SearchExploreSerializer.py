from rest_framework import serializers
from post_app.models import Post, Reel

class PostSearchSerializer(serializers.ModelSerializer):
    type = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = ['id', 'caption', 'location', 'created_at', 'type']

    def get_type(self, obj):
        return 'post'

class ReelSearchSerializer(serializers.ModelSerializer):
    type = serializers.SerializerMethodField()

    class Meta:
        model = Reel
        fields = ['id', 'caption', 'music_track', 'created_at', 'type']

    def get_type(self, obj):
        return 'reel'
