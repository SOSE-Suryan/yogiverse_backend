from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
# from helper_app.views import PermissionValidator
from rest_framework.exceptions import ValidationError, PermissionDenied
from django.utils import timezone
from rest_framework import status
from .models import *
from .serializers import *
from user_app.models import UserModel
from helper_app.paginations import (DefaultPaginationClass,ChatDefaultPaginationClass)
from user_app.serializers import ChatEmployeeSerializer
from django.db.models import Q
from django.db.models import Count
# from helper_app.fcm_push_notify import send_push_notification
from django.shortcuts import get_object_or_404
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from rest_framework.parsers import MultiPartParser, FormParser
from django.db.models import Max

# Create your views here.


class ChatAPI(APIView,ChatDefaultPaginationClass):
    
    # parser_classes = [MultiPartParser, FormParser]
    
    def get(self, request, id=None, format=None):
        
        # if PermissionValidator.is_admin(request.user) or PermissionValidator.is_employee(request.user):
        if request.user.is_authenticated:
            is_user = UserModel.objects.filter(id=request.user.id)
            if is_user.exists() :
                search_chat = request.GET.get('search_chat')
                if id is not None:
                    try:
                        chat_data = ChatModel.objects.get(chat_id=id)
                        # if request.user in chat_data.deleted_for.all():
                        #     return Response({'status': False, 'message': 'Chat not found!'}, status=status.HTTP_404_NOT_FOUND)
                        serializer = ChatSerializer(chat_data,context = {'request':request})
                        return Response({"status": True, "chat": serializer.data}, status=status.HTTP_200_OK)
                    except Exception as e:
                        return Response({'status': False, 'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)
                
                chat_data = (
                            ChatModel.objects
                            .filter(members__in=is_user)
                            .exclude(deleted_for=request.user)
                            .annotate(last_message_time=Max('messages__sent_at'))  # Use your MessageModel related_name and time field
                            .order_by('-last_message_time')
                            )

                if search_chat:
                    chat_data = ChatModel.objects.filter(group_name__icontains=search_chat,members__in= is_user).exclude(deleted_for=request.user)
                    paginated_chats = self.paginate_queryset(chat_data, request, view=self)
                    serializer = ChatSerializer(paginated_chats,context = {'request':request},many=True)
                    paginated_response = self.get_paginated_response(serializer.data).data
                    return Response({"status": True, "groups": serializer.data, 'total_pages': paginated_response.get('total_pages'), 'count': paginated_response.get('count')}, status=status.HTTP_200_OK)
                # chat_data  = ChatModel.objects.filter(members__in=is_user).exclude(deleted_for=request.user).order_by('created_on')
                # ch_data = list()
                # group_chat = list(chat_data.filter(is_single_chat=False))
                # single_chat = chat_data.filter(is_single_chat=True)
                # for i in single_chat:
                #     if i.all_messages1 > 0 and i.is_single_chat == True:
                #         ch_data.append(i)
                # final_chat_list = group_chat + ch_data
                                 
                paginated_chats = self.paginate_queryset(chat_data, request, view=self)
                serializer = ChatSerializer(paginated_chats,context = {'request':request},many=True)
                paginated_response = self.get_paginated_response(serializer.data).data
                return Response({"status": True, "groups": serializer.data, 'total_pages': paginated_response.get('total_pages'), 'count': paginated_response.get('count')}, status=status.HTTP_200_OK)
                # return Response({"status": True, "groups": serializer.data, }, status=status.HTTP_200_OK)
            else:
                return Response({"status": False, 'message': "User does not exist"}, status=status.HTTP_200_OK)
        else:
            return Response({'status': False, 'message': 'Login is required'}, status=status.HTTP_401_UNAUTHORIZED)

    def post(self, request):
        if not request.user.is_authenticated:
            return Response({'status': False, 'message': 'Login is required'}, status=status.HTTP_401_UNAUTHORIZED)

        group_icon = request.FILES.get('group_icon')
        serializer = ChatSerializer(data=request.data, context={'request': request})
        if not serializer.is_valid():
            return Response({"status": False, "message": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        # --------- GROUP CHAT CREATION ----------
        group_name = request.data.get('group_name')
        if group_name:            
            # Check if group already exists
            chat = ChatModel.objects.filter(group_name__icontains=group_name).first()
            if chat:
                # if request.user not in chat.admins.all():
                #     return Response({'status': False, 'message': 'Only admins can perform this action.'}, status=status.HTTP_403_FORBIDDEN)
                members = chat.members.all()
                # member_list = members.values('id', 'first_name', 'last_name','username')
                member_list = [
                            {   'id': m.id, 
                                'first_name': m.first_name,
                                'last_name': m.last_name,
                                'username': m.username,
                                'type': 'admin' if m.id == request.user.id else 'member',
                                'profile_picture': (
                                    request.build_absolute_uri(m.profile.profile_picture.url)
                                    if hasattr(m, 'profile') and m.profile.profile_picture else None
                                )
                            }
                                for m in members
                            ]
                return Response({
                    "status": True, "message": "Group already exists!",
                    "data": {
                        "id": chat.id,
                        "chat_id": chat.chat_id,
                        "group_name": chat.group_name,
                        "group_members": {'group_members': list(member_list), 'total_members': members.count()},
                        "total_members": members.count(),
                    }
                }, status=status.HTTP_200_OK)

            # Add current user to members if not already included
            member_ids = serializer.validated_data['members']

            if request.user.id not in member_ids:
                member_ids.append(request.user.id)
            chat_instance = serializer.save(created_by=request.user)
            chat_instance.admins.add(request.user)
            if group_icon:
                chat_instance.group_icon = group_icon
                chat_instance.save()
            chat_data = ChatSerializer(chat_instance, context={'request': request}).data
            return Response({
                "status": True, "message": "Chat successfully added",
                "data": {
                    "id": chat_data.get("id"),
                    "chat_id": chat_data.get("chat_id"),
                    "group_name": chat_data.get("group_name"),
                    "group_icon":chat_data.get("group_icon"),
                    "members": chat_data.get("members"),
                    "total_members": chat_data.get("group_members").get("total_members") if chat_data.get("group_members") else 0
                }
            }, status=status.HTTP_201_CREATED)

        # --------- SINGLE CHAT CREATION ----------
        else:
            member_ids = serializer.validated_data['members']
        
            if len(member_ids) != 1:
                return Response({"status": False, "message": "For single chat, provide exactly one other user ID in 'members'."}, status=status.HTTP_400_BAD_REQUEST)

            other_user_id = member_ids[0].id
            current_user_id = request.user.id

            # Check if single chat already exists (regardless of order)
            existing_chat = ChatModel.objects.filter(
                is_single_chat=True,
                members__id=current_user_id
            ).filter(
                members__id=other_user_id
            ).first()
            if existing_chat:
                members = existing_chat.members.all()
                member_list = members.values('id', 'first_name', 'last_name', 'phone_no', 'email')
                return Response({
                    "status": True, "message": "Chat already exists!",
                    "data": {
                        "id": existing_chat.id,
                        "chat_id": existing_chat.chat_id,
                        "group_name": existing_chat.group_name,
                        "chat_name": existing_chat.group_name,
                        "group_members": {'group_members': list(member_list), 'total_members': members.count()},
                        "total_members": members.count(),
                    }
                }, status=status.HTTP_200_OK)

            # Create the chat
            if current_user_id not in member_ids:                                
                member_ids.append(current_user_id)

            group_name = f"{UserModel.objects.get(id=other_user_id).first_name} {UserModel.objects.get(id=other_user_id).last_name} | {request.user.first_name} {request.user.last_name}"

            serializer.validated_data['group_name'] = group_name
            serializer.validated_data['is_single_chat'] = True
            chat_instance = serializer.save(created_by=request.user)
            chat_data = ChatSerializer(chat_instance, context={'request': request}).data
            return Response({
                "status": True, "message": "Chat successfully added",
                "data": {
                    "id": chat_data.get("id"),
                    "chat_id": chat_data.get("chat_id"),
                    "chat_name": chat_data.get("chat_name"),
                    "group_name": chat_data.get("group_name"),
                    "group_members": chat_data.get("group_members"),
                    "total_members": chat_data.get("group_members").get("total_members") if chat_data.get("group_members") else 0
                }
            }, status=status.HTTP_201_CREATED)


    def patch(self, request, id=None):
        if not request.user.is_authenticated:
            return Response({'status': False, 'message': 'Login is required'}, status=status.HTTP_401_UNAUTHORIZED)

        try:
            chat = ChatModel.objects.get(chat_id=id, is_single_chat=False)
        except ChatModel.DoesNotExist:
            return Response({'status': False, 'message': 'Group chat not found.'}, status=status.HTTP_404_NOT_FOUND)

        # Anyone can update group name/icon
        if 'group_name' in request.data:
            chat.group_name = request.data['group_name']
        if 'group_icon' in request.FILES:
            chat.group_icon = request.FILES['group_icon']
        elif 'group_icon' in request.data and not request.data['group_icon']:
            # If group_icon is set to "" or null, remove the icon
            chat.group_icon = None
            
        # Only admin can add members
        # add_members = request.data.get('members')
        # if add_members:
        #     if request.user not in chat.admins.all():
        #         return Response({'status': False, 'message': 'Only admin can add members.'}, status=status.HTTP_403_FORBIDDEN)
                        
        #     for id in add_members:
        #         user = UserModel.objects.filter(id=id).first()
        #         if user: chat.members.add(user)
                
        #     for id in not add_members:
        #         user = UserModel.objects.filter(id=id).first()
        #         if user: chat.members.remove(user)

        member_ids = request.data.get('members')
        if member_ids is not None:
            if request.user not in chat.admins.all():
                return Response({'status': False, 'message': 'Only admin can update members.'}, status=status.HTTP_403_FORBIDDEN)
            admin_id = request.user.id
            new_member_ids = set(map(int, member_ids))
            if admin_id not in new_member_ids:
                return Response({'status': False, 'message': "Admin can't remove themselves."}, status=status.HTTP_400_BAD_REQUEST)
            # Set members exactly to provided list (including admin)
            chat.members.set(new_member_ids)
        
        chat.save()
        return Response({'status': True, 'message': 'Group updated.', 'data': ChatSerializer(chat, context={'request': request}).data}, status=status.HTTP_200_OK)
                        
        
    def delete(self, request, id=None, format=None):
        # if PermissionValidator.is_admin(request.user) or PermissionValidator.is_employee(request.user):
        if request.user.is_authenticated:
            # is_user = UserModel.objects.filter(id=request.user.id)
            # if is_user.exists():
            # user_chats = ChatModel.objects.get(id=id)
                # user_chats.delete()
            try:
                chat = ChatModel.objects.get(chat_id=id)
            except ChatModel.DoesNotExist:
                return Response({'status': False, 'message': 'Chat not found!'}, status=status.HTTP_404_NOT_FOUND) 
                
            if request.user not in chat.members.all():
                return Response({'status': False, 'message': 'You are not a member of this chat.'}, status=status.HTTP_403_FORBIDDEN)
            
            if not chat.is_single_chat:
                chat.members.remove(request.user)
                chat.deleted_for.remove(request.user)  # in case user had previously soft-deleted
                if chat.members.count() == 0:
                    chat.delete()
                    return Response({"status": True, 'message': "Group chat deleted as no members left."}, status=status.HTTP_200_OK)
                return Response({"status": True, 'message': "You have left the group chat."}, status=status.HTTP_200_OK)

            # SINGLE CHAT LOGIC
            elif chat.is_single_chat:
                chat.deleted_for.add(request.user)
                # If all members have deleted the chat, remove it from DB
                all_members = chat.members.all()
                deleted_users = chat.deleted_for.all()
                if set(all_members) == set(deleted_users):
                    chat.delete()
                    return Response({"status": True, 'message': "Chat deleted permanently."}, status=status.HTTP_200_OK)
                return Response({"status": True, 'message': "Chat deleted for you."}, status=status.HTTP_200_OK)

            # return Response({"status": True, 'message': "Chat successfully deleted!"}, status=status.HTTP_200_OK)
            # return Response({'status': False, 'message': 'Chat not found!'}, status=status.HTTP_404_NOT_FOUND)
        else:
            return Response({'status': False, 'message': 'Login is required'}, status=status.HTTP_401_UNAUTHORIZED)




class ReadChatMsgAPI(APIView,DefaultPaginationClass):
    def get(self, request, id=None, format=None):
        
        # if PermissionValidator.is_admin(request.user) or PermissionValidator.is_employee(request.user):
        if request.user.is_authenticated:
            is_user = UserModel.objects.filter(id=request.user.id)
            is_emp = UserModel.objects.filter(id=request.user.id)
            if is_user.exists() and is_emp.exists():
                if id is not None:
                    try:
                        chat_data = ChatModel.objects.get(id=id)
                        all_messages = chat_data.messages.all()
                        
                        #changes made on 28-01-2025
                        try:
                            all_messages = all_messages.exclude(sender=is_emp[0])
                        except Exception as e:
                            print(e)
                            all_messages = chat_data.messages.all()
                        ###
                        
                        all_messages.update(is_read=True)
                        # serializer = MessageSerializer(all_messages, many=True, context = {'request':request})
                        #  "chat": serializer.data,
                        return Response({"status": True, "message":"All messages have been read"}, status=status.HTTP_200_OK)
                    except Exception as e:
                        return Response({'status': False, 'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)
                return Response({"status": False, 'message': "Chat id is required!"}, status=status.HTTP_200_OK)
                # return Response({"status": True, "groups": serializer.data, 'total_pages': paginated_response.get('total_pages'), 'count': paginated_response.get('count')}, status=status.HTTP_200_OK)
            else:
                return Response({"status": False, 'message': "User does not exist"}, status=status.HTTP_200_OK)
        else:
            return Response({'status': False, 'message': 'Login is required'}, status=status.HTTP_401_UNAUTHORIZED)



class MessageAPI(APIView):
    def post(self, request):
        if request.user.is_authenticated:
            try:
                emp_obj = UserModel.objects.get(id=request.user.id)
                chat_obj = ChatModel.objects.get(id=request.data.get('chat'))

                if request.FILES.get('files') is None and request.data.get('message') is None:
                    return Response({"status": False, "message": "Enter message or file for send!"}, status=status.HTTP_400_BAD_REQUEST)

                serializer = MessageSerializer(data=request.data, context={'request': request})
                if serializer.is_valid():
                    if request.FILES.get('files'):
                        file_obj = ChatAttachmentModel.objects.create(
                            sender=emp_obj,
                            chat=chat_obj,
                            attachment=request.data.get('files')
                        )
                        msg = serializer.save(sender=emp_obj, files_attachment=file_obj)
                    else:
                        msg = serializer.save(sender=emp_obj)

                    # Broadcast to WebSocket group
                    channel_layer = get_channel_layer()
                    chat_group_name = f"chat_{chat_obj.chat_id}"
                    serialized_msg = MessageSerializer(msg, context={'request': request}).data
                    async_to_sync(channel_layer.group_send)(
                        chat_group_name,
                        {
                            "type": "chat_message",
                            "message": serialized_msg,
                        }
                    )

                    # Existing notification logic...
                    get_chat = ChatModel.objects.get(id=msg.chat.id)
                    chat_serializer = ChatSerializer(get_chat, context={'request': request}).data
                    all_members = get_chat.members.exclude(id=emp_obj.id)
                    body_data = {
                        "notification": {
                            "body": msg.message,
                            "title": f"{msg.sender.first_name} {msg.sender.last_name}",
                            "chat_id": chat_serializer.get('id'),
                            "chat_uuid": chat_serializer.get('chat_id'),
                            "group_name": chat_serializer.get('chat_name'),
                            "total_members": len(get_chat.members.all()),
                            "priority": "high"
                        },
                        "aps": {
                            "alert": msg.message,
                            "badge": 1,
                        },
                        "data": {
                            "body": msg.message,
                            "title": f"{msg.sender.first_name} {msg.sender.last_name}",
                            "chat_id": chat_serializer.get('id'),
                            "chat_uuid": chat_serializer.get('chat_id'),
                            "group_name": chat_serializer.get('chat_name'),
                            "total_members": len(get_chat.members.all()),
                            "priority": "high"
                        }
                    }
                    for i in all_members:
                        fcm_tokens = FCMTokenModel.objects.filter(employee=i)
                        if fcm_tokens.exists():
                            pass  # Add your push notification logic here

                    return Response({"status": True, "message": "Message sent!"}, status=status.HTTP_201_CREATED)
                else:
                    return Response({"status": False, "message": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
            except Exception as e:
                from traceback import format_exc
                print(format_exc(e))
                return Response({"status": False, "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({'status': False, 'message': 'Login is required'}, status=status.HTTP_401_UNAUTHORIZED)

    def delete(self, request, id=None, format=None):
        # if PermissionValidator.is_admin(request.user) or PermissionValidator.is_employee(request.user):
        if request.user.is_authenticated:
            try:
                
                if id is not None:
                    msg = MessageModel.objects.get(id=id)
                    if msg.files_attachment is not None:
                        chat_id = msg.files_attachment
                        chat_id.delete()
                    msg.delete()
                    return Response({"status": True, "message": "Message deleted!"}, status=status.HTTP_200_OK)
                else:
                    return Response({"status": False, "message": "Message not found!"}, status=status.HTTP_404_NOT_FOUND)
            except Exception as e:
                return Response({"status": False, "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({"status": False, "message": "Unauthorized"}, status=status.HTTP_401_UNAUTHORIZED)


class ChatAttachmentAPI(APIView, DefaultPaginationClass):
    def post(self, request):        
        if request.user.is_authenticated:
            try:
                chat = ChatModel.objects.get(chat_id=request.data.get('chat'))
                emp = UserModel.objects.get(id=request.user.id)
                files = request.data.getlist("attachments")
                if len(files) > 0:
                    for file in files:
                        saved_file = ChatAttachmentModel.objects.create(
                            chat=chat, sender=emp, attachment=file)
                        MessageModel.objects.create(
                            chat=chat, sender=emp, message=request.build_absolute_uri(saved_file.attachment.url), file=saved_file)
                    return Response({'status': True, 'message': 'Files sent!'}, status=status.HTTP_201_CREATED)
                else:
                    return Response({'status': False, "message": "Upload at least one file!"}, status=status.HTTP_400_BAD_REQUEST)
            except Exception as e:
                from traceback import format_exc
                return Response(e, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            return Response({'status': False, 'message': 'Login is required'}, status=status.HTTP_401_UNAUTHORIZED)

