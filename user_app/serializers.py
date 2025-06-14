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