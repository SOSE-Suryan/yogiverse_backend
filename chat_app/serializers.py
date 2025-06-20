from rest_framework import serializers
from user_app.Serializer.UserSerializer import UserSerializer
from .models import *
from os.path import basename
from django.conf import settings
from user_app.models import FCMTokenModel
from rest_framework.pagination import PageNumberPagination

class ChatMessageCustomPagination(PageNumberPagination):
    page_size = 30  # Change as per your requirement
    page_size_query_param = 'page_size'
    max_page_size = 1000

class ChatMemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserModel
        fields = ['id', 'first_name', 'last_name', 'email', 'phone_no']

class ChatSerializer(serializers.ModelSerializer):
    members = serializers.PrimaryKeyRelatedField(
        queryset=UserModel.objects.all(),
        many=True,
        required=True,
    )
    group_members = serializers.SerializerMethodField(read_only=True)
    chat_name = serializers.SerializerMethodField()
    all_messages = serializers.SerializerMethodField()
    unread_messages = serializers.SerializerMethodField()
    
    def create(self, validated_data):
        members = validated_data.pop('members', [])
        chat = ChatModel.objects.create(**validated_data)
        chat.members.set(members)  # FIX: set expects a list of IDs or objects, not members.id
        chat.save()
        return chat

    def get_group_members(self, obj):
        members = obj.members.all()
        serializer = ChatMemberSerializer(members, many=True)
        return {
            'members': serializer.data,
            'total_members': members.count()
        }

    def get_chat_name(self, obj):
        """
        For single chat: Returns other member's full name.
        For group chat: Returns group_name.
        """
        request = self.context.get('request')
        current_user = request.user if request else None

        if obj.is_single_chat and current_user:
            # Return the other member's name
            other_members = obj.members.exclude(id=current_user.id)
            if other_members.exists():
                other = other_members.first()
                return f"{other.first_name} {other.last_name}"
            return obj.group_name or ""
        return obj.group_name or ""

    def get_all_messages(self, obj):
        # Example stub: Replace with your MessageSerializer and pagination if needed
        return obj.messages.count()

    def get_unread_messages(self, obj):
        request = self.context.get('request')
        current_user = request.user if request else None
        if current_user:
            return obj.messages.filter(is_read=False).exclude(sender=current_user).count()
        return obj.messages.filter(is_read=False).count()

    class Meta:
        model = ChatModel
        fields = [
            'id', 'chat_id', 'group_name','group_members','is_single_chat', 'created_on', 'updated_at',
            'created_by', 'members', 'chat_name', 'all_messages', 'unread_messages'
        ]

class MessageSerializer(serializers.ModelSerializer):
    sent_by = serializers.SerializerMethodField(read_only=True)
    attachment_data = serializers.SerializerMethodField(read_only=True)

    def get_sent_by(self, obj):
        return obj.sender.__str__()

    def get_attachment_data(self, obj):
        request = self.context.get('request')
        attachments = obj.files_attachment.all()
        if attachments:
            data = []
            for attachment in attachments:
                if request:
                    file_url = request.build_absolute_uri(attachment.attachment.url)
                    file_url_https = file_url.replace('http://', 'https://')
                else:
                    file_url_https = attachment.attachment.url
                data.append({'file_name': basename(file_url_https), 'file_url': file_url_https})
            return data
        return []

    class Meta:
        model = MessageModel
        fields = "__all__"


class ChatAttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatAttachmentModel
        fields = "__all__"
