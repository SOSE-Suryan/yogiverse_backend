from rest_framework import serializers
from .models import Follower, FirebaseNotification
from django.contrib.auth import get_user_model

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    profile_picture = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'profile_picture', 'first_name', 'last_name']
    
    def get_profile_picture(self, obj):
        if hasattr(obj, 'profile') and obj.profile.profile_picture:
            return obj.profile.profile_picture.url
        return None

class FollowerSerializer(serializers.ModelSerializer):
    follower = UserSerializer(read_only=True)
    following = UserSerializer(read_only=True)
    following_count = serializers.SerializerMethodField()
    followers_count = serializers.SerializerMethodField()

    class Meta:
        model = Follower
        fields = ['id', 'follower', 'following', 'created_at', 'following_count', 'followers_count']
        read_only_fields = ['created_at']
    
    def get_following_count(self, obj):
        return Follower.objects.filter(follower=obj.follower).count()
    
    def get_followers_count(self, obj):
        return Follower.objects.filter(following=obj.following).count()

class FirebaseNotificationSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = FirebaseNotification
        fields = ['id', 'user', 'title', 'body', 'data', 'is_read', 'created_at']
        read_only_fields = ['created_at'] 