from channels.consumer import AsyncConsumer, StopConsumer
from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
import json
import base64
from django.core.files.base import ContentFile
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AsyncChatConsumer(AsyncConsumer):
    async def websocket_connect(self, event):
        self.chat_id = self.scope["url_route"]["kwargs"]["chat_id"]
        self.chat_group_name = f"chat_{self.chat_id}"

        # Add the user to the chat group
        await self.channel_layer.group_add(
            self.chat_group_name,
            self.channel_name
        )
        await self.send({
            "type": "websocket.accept",
        })

    @database_sync_to_async
    def returnUser(self, token):
        from django.contrib.auth.models import AnonymousUser  # moved import here to avoid AppRegistryNotReady
        from rest_framework_simplejwt.authentication import JWTAuthentication
        from rest_framework_simplejwt.exceptions import InvalidToken, AuthenticationFailed
        try:
            validated_token = JWTAuthentication().get_validated_token(token)
            user = JWTAuthentication().get_user(validated_token)
            return user
        except (InvalidToken, AuthenticationFailed):
            return AnonymousUser()

    @database_sync_to_async
    def getLatestMessages(self):
        from .models import MessageModel
        from .serializers import MessageSerializer

        if not self.chat_id:
            return json.dumps({"error": "Chat ID is required"})
        
        MessageModel.objects.filter(chat__chat_id=self.chat_id).update(is_read=True)
        
        latest_messages = MessageModel.objects.filter(chat__chat_id=self.chat_id).order_by('sent_at')
        serializer = MessageSerializer(latest_messages, many=True, context={'request': None})
        return json.dumps(serializer.data)

    @database_sync_to_async
    def save_message(self, message_content, employee, conversation, files=None,message_type=None, mention_link=None):
        from .models import MessageModel, ChatAttachmentModel
        from django.conf import settings
        message = MessageModel.objects.create(
            message=message_content,
            sender=employee,
            chat=conversation,
            message_type=message_type
        )
        if files:
            for file_data in files: 
                name = file_data['name']
                data = file_data['data']
                if ',' in data:
                    data = data.split(',')[1]
                file_content = ContentFile(base64.b64decode(data), name=name)
                file_obj = ChatAttachmentModel.objects.create(
                    sender=employee,
                    chat=conversation,
                    attachment=file_content  # expects FileField
                )
                message.files_attachment.add(file_obj)
            message.save()
        return message


    @database_sync_to_async
    def serialize_message(self, message):
        from .serializers import MessageSerializer
        serializer = MessageSerializer(message, context={'request': None})
        return serializer.data

    async def websocket_receive(self, event):
        import json
        query_dict = json.loads(event.get('text', '{}'))
        if not query_dict:
            return

        token = query_dict.get('token')
        if not token:
            await self.send({"type": "websocket.send", "text": json.dumps({"error": "Token required"})})
            raise StopConsumer()

        user = await self.returnUser(token)
        from django.contrib.auth.models import AnonymousUser  # import here for isinstance check
        if isinstance(user, AnonymousUser):
            await self.send({"type": "websocket.send", "text": json.dumps({"error": "Invalid token"})})
            raise StopConsumer()

        query_type = query_dict.get('queryType')
        if query_type == "get_messages":
            latest_messages = await self.getLatestMessages()
            await self.send({
                "type": "websocket.send",
                "text": latest_messages,
            })
        elif query_type == "send_message":
            message_content = query_dict.get('content')
            files = query_dict.get('files', None)
            message_type = query_dict.get('message_type', None)
            
            logger.info(f"Received message content: {message_content}, files: {files}, message_type: {message_type}")
            logger.info(f"message_type: {message_type}")

            try:
                from user_app.models import UserModel
                from .models import ChatModel
                employee = await database_sync_to_async(UserModel.objects.get)(id=user.id)
                conversation = await database_sync_to_async(ChatModel.objects.get)(chat_id=self.chat_id)
                message = await self.save_message(message_content, employee, conversation,
                                                  files=files,
                                                  message_type=message_type
                                                  )
                serialized_data = await self.serialize_message(message)

                # Broadcast the message to the group
                await self.channel_layer.group_send(
                    self.chat_group_name,
                    {
                        "type": "chat_message",
                        "message": serialized_data,
                    }
                )
            except Exception as e:
                await self.send({
                    "type": "websocket.send",
                    "text": json.dumps({"error": str(e)}),
                })

    async def chat_message(self, event):
        # Send message to WebSocket clients
        await self.send({
            "type": "websocket.send",
            "text": json.dumps(event["message"]),
        })

    async def websocket_disconnect(self, close_code):
        print(f"Disconnected: {close_code}")
        await self.channel_layer.group_discard(
            self.chat_group_name,
            self.channel_name
        )
        raise StopConsumer()
