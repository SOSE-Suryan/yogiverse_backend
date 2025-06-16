from rest_framework import serializers
from .models import *

class ChatEmployeeSerializer(serializers.ModelSerializer):
    user_id = serializers.StringRelatedField()
    first_name = serializers.SerializerMethodField(read_only=True)
    last_name = serializers.SerializerMethodField(read_only=True)
    def get_first_name(self, obj):
        if obj.user_id:
            user = UserModel.objects.get(email=obj.user_id)
            return user.first_name
        elif obj.first_name:
            return obj.first_name
        else:
            return ''

    def get_last_name(self, obj):
        if obj.user_id:
            user = UserModel.objects.get(email=obj.user_id)
            return user.last_name
        elif obj.last_name:
            return obj.last_name
        else:
            return ''

    class Meta:
        model = UserModel
        # fields = '__all__'
        exclude = ["allowed_companies"]
        

class FCMTokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = FCMTokenModel
        fields = ['device_type', 'token', 'device_name']
        
    def create(self, validated_data):
        user = self.context.get('user')
        if not user or not user.is_authenticated:
            raise serializers.ValidationError("User must be authenticated")
        
        validated_data['user'] = user
        token = validated_data.get('token')
        device_type = validated_data.get('device_type', 'web')
        device_name = validated_data.get('device_name', 'Unknown Device')
        
        # Check if token already exists for this user
        existing_token = FCMTokenModel.objects.filter(
            user=user,
            token=token,
            device_type=device_type
        ).first()
        
        if existing_token:
            # Update the existing token
            existing_token.device_name = device_name
            existing_token.save()
            return existing_token
            
        # Create new token if it doesn't exist
        return FCMTokenModel.objects.create(**validated_data)
    
    