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

class ChatSerializer(serializers.ModelSerializer):
    group_members = serializers.SerializerMethodField(read_only=True)
    # group_members = ChatEmployeeSerializer(source='members',many=True)
    all_messages = serializers.SerializerMethodField(read_only=True)
    unread_messages = serializers.SerializerMethodField(read_only=True)
    chat_name = serializers.SerializerMethodField(read_only=True)

    def get_group_members(self, obj):
        request = self.context.get('request')
        full_domain = request.build_absolute_uri('/')[:-1]
        media_url = settings.MEDIA_URL
        members = obj.members.all()
        member_list = members.values('id','user_id__first_name','user_id__last_name','work_mobile_no','work_phone','work_mail','profile_image')
        for i in member_list:
            if i['profile_image']:
                i.update({'profile_image':full_domain + media_url + i['profile_image']})
        return {'group_members':member_list,'total_members':len(members)}
    
    def get_all_messages(self, obj):
        request = self.context.get('request')
        mesg = obj.messages.all().order_by('-sent_at')
        # serializer = MessageSerializer(mesg, many=True, context={'request': request})
        # return serializer.data
        # ============ pagination logic start ===================
        paginator = ChatMessageCustomPagination()
        paginated_messages = paginator.paginate_queryset(mesg, request)
        serializer = MessageSerializer(paginated_messages, many=True, context={'request': request})
        paginated_response = paginator.get_paginated_response(serializer.data).data
        res = {'all_messages':list(reversed(serializer.data)),'total_messages':mesg.count(), 'total_pages': paginated_response.get('total_pages'), 'count': paginated_response.get('count')}
        return res
        # ============ pagination logic end ===================
    
    def get_unread_messages(self, obj):
        request = self.context.get('request')
        unread_mesg = obj.messages.filter(is_read=False).count()
        
        #changes made on 28-01-2025
        is_emp = UserSerializer.objects.filter(user_id=request.user)                
        try:
            unread_mesg = obj.messages.filter(is_read=False).exclude(sender=is_emp[0]).count()
        except Exception as e:
            print(e)
            unread_mesg = obj.messages.filter(is_read=False).count()
        ############################
        
        return unread_mesg
    
    def get_chat_name(self, obj):
        request = self.context.get('request')
        emp = UserSerializer.objects.filter(user_id=request.user)
        chat = ChatModel.objects.filter(chat_id=obj.chat_id)
        full_name = ""
        if chat.exists():
            chat_instance = chat[0]
            if chat_instance.is_single_chat:
                mem_list = [i for i in chat_instance.members.all()]
                if mem_list:
                    if emp.exists() and emp[0] in mem_list:
                        mem_list.remove(emp[0])
                        if mem_list:
                            full_name = f"{mem_list[0].user_id.first_name} {mem_list[0].user_id.last_name}"
                        else:
                            full_name = chat_instance.group_name
            else:
                full_name = chat_instance.group_name
        return full_name.capitalize()

    class Meta:
        model = ChatModel
        fields = "__all__"



class MessageSerializer(serializers.ModelSerializer):
    sent_by = serializers.SerializerMethodField(read_only=True)
    attachment_data = serializers.SerializerMethodField(read_only=True)

    def get_sent_by(self, obj):
        return obj.sender.__str__()

    # def get_attachment_data(self, obj):
    #     request = self.context.get('request')
    #     if obj.files_attachment:
    #         print(request.build_absolute_uri(obj.files_attachment.attachment.url))
    #         return {'file_name':basename(request.build_absolute_uri(obj.files_attachment.attachment.url)),'file_url':request.build_absolute_uri(obj.files_attachment.attachment.url)}


    def get_attachment_data(self, obj):
        request = self.context.get('request')
        if obj.files_attachment:
            file_url = request.build_absolute_uri(obj.files_attachment.attachment.url)
            # Replace 'http://' with 'https://'
            file_url_https = file_url.replace('http://', 'https://')
            return {'file_name': basename(file_url_https), 'file_url': file_url_https}        

    class Meta:
        model = MessageModel
        fields = "__all__"


class ChatAttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatAttachmentModel
        fields = "__all__"

class FCMTokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = FCMTokenModel
        fields = "__all__"
