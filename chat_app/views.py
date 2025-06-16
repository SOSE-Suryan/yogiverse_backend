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
# Create your views here.


class PermissionValidator:
    def is_admin(user):
        return user.is_authenticated and user.is_superuser

    def is_employee(user):
        return user.is_authenticated and user.is_staff 

class ChatAPI(APIView,ChatDefaultPaginationClass):
    def get(self, request, id=None, format=None):
        
        # if PermissionValidator.is_admin(request.user) or PermissionValidator.is_employee(request.user):
        if request.user.is_authenticated:
            is_user = UserModel.objects.filter(id=request.user.id)
            is_emp = UserModel.objects.filter(user_id=request.user)
            if is_user.exists() and is_emp.exists():
                search_chat = request.GET.get('search_chat')
                if id is not None:
                    try:
                        chat_data = ChatModel.objects.get(id=id)
                        serializer = ChatSerializer(chat_data,context = {'request':request})
                        return Response({"status": True, "chat": serializer.data}, status=status.HTTP_200_OK)
                    except Exception as e:
                        return Response({'status': False, 'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)
                
                if search_chat:
                    # chat_data =ChatModel.objects.filter(members__in=is_emp)
                    chat_data = ChatModel.objects.filter(group_name__icontains=search_chat,members__in= is_emp)
                    paginated_chats = self.paginate_queryset(chat_data, request, view=self)
                    serializer = ChatSerializer(paginated_chats,context = {'request':request},many=True)
                    paginated_response = self.get_paginated_response(serializer.data).data
                    return Response({"status": True, "groups": serializer.data, 'total_pages': paginated_response.get('total_pages'), 'count': paginated_response.get('count')}, status=status.HTTP_200_OK)
                chat_data  = ChatModel.objects.filter(members__in=is_emp).order_by('-id')
                ch_data = list()
                group_chat = list(chat_data.filter(is_single_chat=False))
                single_chat = chat_data.filter(is_single_chat=True)
                for i in single_chat:
                    if i.all_messages1 > 0 and i.is_single_chat == True:
                        ch_data.append(i)
                final_chat_list = group_chat + ch_data
                paginated_chats = self.paginate_queryset(final_chat_list, request, view=self)
                serializer = ChatSerializer(paginated_chats,context = {'request':request},many=True)
                paginated_response = self.get_paginated_response(serializer.data).data
                return Response({"status": True, "groups": serializer.data, 'total_pages': paginated_response.get('total_pages'), 'count': paginated_response.get('count')}, status=status.HTTP_200_OK)
                # return Response({"status": True, "groups": serializer.data, }, status=status.HTTP_200_OK)
            else:
                return Response({"status": False, 'message': "User does not exist"}, status=status.HTTP_200_OK)
        else:
            return Response({'status': False, 'message': 'Login is required'}, status=status.HTTP_401_UNAUTHORIZED)

    def post(self, request):
        # if PermissionValidator.is_admin(request.user) or PermissionValidator.is_employee(request.user):
        if request.user.is_authenticated:
            serializer = ChatSerializer(data=request.data,context = {'request':request})
            if serializer.is_valid():
                if request.data.get('group_name') is not None:
                    chat = ChatModel.objects.filter(group_name__contains=request.data.get('group_name'))
                    if chat.exists():
                        mem = chat[0].members.all()
                        member_list = mem.values('id','user_id__first_name','user_id__last_name','work_mobile_no','work_phone','work_mail')
                        return Response({
                            "status": True, "message": "Group already exist!",
                            "data":{
                                "id": chat[0].id,
                                "chat_id": chat[0].chat_id,
                                "group_name": chat[0].group_name,
                                "group_members": {'group_members':member_list,'total_members':len(mem)},
                                "total_members": len(chat[0].members.all())
                            }

                        }, status=status.HTTP_200_OK)
                    serializer.validated_data['members'].append(UserModel.objects.get(user_id=request.user).id)
                    serializer.save(created_by=UserModel.objects.get(user_id=request.user))
                    chat_data = serializer.data
                    return Response({
                        "status": True, "message": "Chat successfully added",
                        "data":{
                                "id": chat_data.get("id"),
                                "chat_id": chat_data.get("chat_id"),
                                "group_name": chat_data.get("group_name"),
                                "group_members": chat_data.get("id"),
                                "total_members": chat_data.get("group_members").get("total_members")
                            }
                    }, status=status.HTTP_201_CREATED)
                else:
                    
                    if len(serializer.validated_data['members']) > 1:
                        return Response({"status": False, "message": "Not allowd more then one person"}, status=status.HTTP_400_BAD_REQUEST)
                    member1 = serializer.validated_data['members'][0]
                    member2 = UserModel.objects.get(user_id=request.user)
                    chat = ChatModel.objects.filter(members=member1).filter(members=member2).filter(is_single_chat=True).first()
                    chat_seria = ChatSerializer(chat,context = {'request':request}).data
                    if chat is not None:
                        mem = chat.members.all()
                        member_list = mem.values('id','user_id__first_name','user_id__last_name','work_mobile_no','work_phone','work_mail')
                        
                        return Response({
                            "status": True, "message": "Chat already exist!",
                            "data":{
                                "id": chat.id,
                                "chat_id": chat.chat_id,
                                "group_name": chat.group_name,
                                "chat_name": chat_seria.get("chat_name"),
                                "group_members": {'group_members':member_list,'total_members':len(mem)},
                                "total_members": len(chat.members.all())
                            }

                        }, status=status.HTTP_200_OK)
                    
                    else:

                        serializer.validated_data['members'].append(UserModel.objects.get(user_id=request.user).id)
                        emp =UserModel.objects.get(id=serializer.validated_data['members'][0].id)
                        serializer.validated_data['group_name'] = f"{emp.user_id.first_name} {emp.user_id.last_name} | {request.user.first_name} {request.user.last_name}"
                        serializer.validated_data['is_single_chat'] = True
                        serializer.save(created_by=UserModel.objects.get(user_id=request.user))
                        chat_data = serializer.data
                        # print(chat_seria.get("chat_name"),"GGGGGGGGGGGGGGG")
                        return Response({
                            "status": True, "message": "Chat successfully added",
                            "data":{
                                "id": chat_data.get("id"),
                                "chat_id": chat_data.get("chat_id"),
                                "chat_name": chat_data.get("chat_name"),
                                "group_name": chat_data.get("group_name"),
                                "group_members": chat_data.get("id"),
                                "total_members": chat_data.get("group_members").get("total_members")
                            }
                        
                        }, status=status.HTTP_201_CREATED)
            else:
                return Response({"status": False, "message": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({'status': False, 'message': 'Login is required'}, status=status.HTTP_401_UNAUTHORIZED)

    def delete(self, request, id=None, format=None):
        # if PermissionValidator.is_admin(request.user) or PermissionValidator.is_employee(request.user):
        if request.user.is_authenticated:
            is_user = UserModel.objects.filter(id=request.user.id)
            is_emp = UserModel.objects.filter(user_id=request.user)
            if is_user.exists() and is_emp.exists():
                user_chats = ChatModel.objects.get(id=id)
                user_chats.delete()
                
                return Response({"status": True, 'message': "Chat successfully deleted!"}, status=status.HTTP_200_OK)
            return Response({"status": False, 'message': "Something went wrong!"}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({'status': False, 'message': 'Login is required'}, status=status.HTTP_401_UNAUTHORIZED)




class ReadChatMsgAPI(APIView,DefaultPaginationClass):
    def get(self, request, id=None, format=None):
        
        # if PermissionValidator.is_admin(request.user) or PermissionValidator.is_employee(request.user):
        if request.user.is_authenticated:
            is_user = UserModel.objects.filter(id=request.user.id)
            is_emp = UserModel.objects.filter(user_id=request.user)
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
        # if PermissionValidator.is_admin(request.user) or PermissionValidator.is_employee(request.user):
        if request.user.is_authenticated:
            try:
                emp_obj =UserModel.objects.get(user_id=request.user)
                chat_obj =ChatModel.objects.get(id=request.data.get('chat'))
                
                if request.FILES.get('files') is None and request.data.get('message') is None:
                    return Response({"status": False, "message": "Enter message or file for send!"}, status=status.HTTP_400_BAD_REQUEST)

                serializer = MessageSerializer(data=request.data,context = {'request':request})
                
                if serializer.is_valid():
                    if request.FILES.get('files'):
                        file_obj = ChatAttachmentModel.objects.create(
                            sender = emp_obj,
                            chat = chat_obj,
                            attachment = request.data.get('files')
                        )
                        msg  = serializer.save(sender=emp_obj,files_attachment=file_obj)
                        get_chat =  ChatModel.objects.get(id=msg.chat.id)
                        chat_serializer = ChatSerializer(get_chat, context={'request':request}).data
                        # emp_obj =UserModel.objects.get(user_id=request.user)
                        all_members = get_chat.members.exclude(id=emp_obj.id)
                        # print(all_members)
                        body_data = {
                            "notification": {
                                    "body": msg.message,
                                    "title": f"{msg.sender.user_id.first_name} {msg.sender.user_id.last_name}",
                                    "chat_id": chat_serializer.get('id'),
                                    "group_name": chat_serializer.get('chat_name'),
                                    "total_members": len(chat_serializer.members.all()),
                                    "priority":"high"
                                },
                                "aps" : {
                                    "alert" : f"{msg.sender.user_id.first_name} {msg.sender.user_id.last_name}",
                                    "badge" : 1,
                                },
                                "data": {
                                    "body": msg.message,
                                    "title": f"{msg.sender.user_id.first_name} {msg.sender.user_id.last_name}",
                                    "chat_id": chat_serializer.get('id'),
                                    "group_name": chat_serializer.get('chat_name'),
                                    "total_members": len(chat_serializer.members.all()),
                                    "priority":"high"
                            }
                        }
                        
                        for i in all_members:
                            fcm_tokens = FCMTokenModel.objects.filter(employee=i)
                            if fcm_tokens.exists():
                                pass
                                # try:
                                    # send_push_notification(fcm_tokens.token,body_data.get('notification').get('title'), body_data.get('notification').get('body'),{"body":body_data})
                                
                    else:
                        msg = serializer.save(sender=emp_obj)
                        get_chat =  ChatModel.objects.get(id=msg.chat.id)
                        chat_serializer = ChatSerializer(get_chat, context={'request':request}).data
                        all_members = get_chat.members.exclude(id=emp_obj.id)
                       
                        body_data = {
                            "notification": {
                                    "body": msg.message,
                                    "title": f"{msg.sender.user_id.first_name} {msg.sender.user_id.last_name}",
                                    "chat_id": chat_serializer.get('id'),
                                    "chat_uuid": chat_serializer.get('chat_id'),
                                    "group_name": chat_serializer.get('chat_name'),
                                    "total_members": len(get_chat.members.all()),
                                    "priority":"high"
                                },
                                "aps": {
                                    "alert" : msg.message,
                                    "badge" : 1,
                                },
                                "data": {
                                    "body": msg.message,
                                    "title": f"{msg.sender.user_id.first_name} {msg.sender.user_id.last_name}",
                                    "chat_id": chat_serializer.get('id'),
                                    "chat_uuid": chat_serializer.get('chat_id'),
                                    "group_name": chat_serializer.get('chat_name'),
                                    "total_members": len(get_chat.members.all()),
                                    "priority":"high"
                            }
                        }
                        for i in all_members:
                            from django.forms.models import model_to_dict
                            fcm_tokens = FCMTokenModel.objects.filter(employee=i)
                            # for instance in fcm_tokens:
                                # Convert the model instance to a dictionary
                                # instance_dict = model_to_dict(instance)
                                
                                # Print the fields and their values
                                # for field, value in instance_dict.items():
                                #     print(f"{field}: {value}")
                            if fcm_tokens.exists():
                                pass
        # Assuming you want to use the first token in the QuerySet for sending the notification
                                # first_token_instance = fcm_tokens.first()
                                # send_push_notification(first_token_instance.token, body_data.get('notification').get('title'), body_data.get('notification').get('body'), {"body": body_data})
                                
                            # if fcm_tokens.exists():
                            #     send_push_notification(fcm_tokens.token, body_data.get('notification').get('title'), body_data.get('notification').get('body'),{"body":body_data})

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
        if PermissionValidator.is_admin(request.user) or PermissionValidator.is_employee(request.user):
            try:
                chat = ChatModel.objects.get(chat_id=request.data.get('chat'))
                emp = UserModel.objects.get(user_id__id=request.user.id)
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
            raise PermissionDenied()


class FCMTokenView(APIView):
    def post(self, request):
        if PermissionValidator.is_admin(request.user) or PermissionValidator.is_employee(request.user):
            try:
                emp = UserModel.objects.get(user_id=request.user)
                device_type = request.data.get('device_type')
                print(device_type , "----------------------------------")
                token = request.data.get('token')
                print(token , "-------------------------------")
                if device_type and token:
                    employee = get_object_or_404(UserModel, pk=emp.id)
                    fcm_token, created = FCMTokenModel.objects.update_or_create(
                        employee=employee,
                        defaults={
                            'device_type': device_type,
                            'token': token,
                        }
                    )
                    serializer = FCMTokenSerializer(fcm_token)
                    return Response({'status': True,'data':serializer.data,'message': 'FCM Token updated' if not created else 'FCM Token created'}, status=status.HTTP_200_OK)
                else:
                    return Response({'status': False,'message': 'Device type and token required!'}, status=status.HTTP_400_BAD_REQUEST)
                
            except Exception as e:
                print(str(e))
                return Response({'status': False, 'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        else:
            raise PermissionDenied()
        
        
class NotificationChatAPI(APIView):
    def get(self, request, id=None, format=None):
        
        if PermissionValidator.is_admin(request.user) or PermissionValidator.is_employee(request.user):
            try:
                is_user = UserModel.objects.filter(id=request.user.id)
                is_emp = UserModel.objects.filter(user_id=request.user)
                if is_user.exists() and is_emp.exists():
                    chat_data = ChatModel.objects.filter(members__in=is_emp).order_by('-id')

                    # Filter single chats with messages
                    ch_data = [chat for chat in chat_data if chat.is_single_chat and chat.all_messages1 > 0]
                    
                    # Separate group and single chats
                    group_chat = list(chat_data.filter(is_single_chat=False))
                    final_chat_list = group_chat + ch_data

                    # Calculate total unread messages
                    total_unread_messages = sum(
                        chat.messages.filter(is_read=False).exclude(sender=is_emp.first()).count() for chat in final_chat_list
                    )

                    return Response({
                        "status": True, 
                        "total_unread_messages": total_unread_messages
                    }, status = status.HTTP_200_OK)

                else:
                    return Response({"status": False, "total_unread_messages": 0, 'message': "User does not exist"}, status=status.HTTP_200_OK)
            
            except Exception as e:
                return Response({'status': False, 'total_unread_messages': 0, 'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        else:
            raise PermissionDenied()
        