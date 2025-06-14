from channels.consumer import AsyncConsumer, StopConsumer
from channels.db import database_sync_to_async
from rest_framework.authtoken.models import Token
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, AuthenticationFailed

from django.contrib.auth.models import AnonymousUser
from user_app.models import *
from .models import *
import json
from .serializers import *


# class AsyncChatConsumer(AsyncConsumer):
#     @database_sync_to_async
#     # def returnUser(self, token_key):
#     #     try:
#     #         return Token.objects.get(key=token_key).user
#     #     except Token.DoesNotExist:
#     #         return AnonymousUser()
    
   
#     def returnUser(self, token):
#         try:
#             validated_token = JWTAuthentication().get_validated_token(token)
#             user = JWTAuthentication().get_user(validated_token)
#             return user
#         except (InvalidToken, AuthenticationFailed):
#             return AnonymousUser()


#     @database_sync_to_async
#     def getLatestMessages(self):
#         # latest_messages = []
#         latest_messages = MessageModel.objects.filter(
#             chat__chat_id=self.chat_id)
#         # async for message in messages:
#         serializer = MessageSerializer(
#             latest_messages, many=True)
#         #     latest_messages.append(serializer.data)
#         return json.dumps(serializer.data)

#     async def websocket_connect(self, event):
#         self.chat_id = self.scope["url_route"]["kwargs"]["chat_id"]
#         # self.chat_name = f"chat_{self.chat_id}"
#         # await (self.channel_layer.group_add)(
#         #     self.chat_group_name, self.channel_name
#         # )
#         # await (self.channel_layer.group_add)(
#         #     self.chat_id, self.channel_name
#         # )
#         await self.send({
#             "type": "websocket.accept",
#         })

#     @database_sync_to_async
#     def save_message(self, message, employee, conversation):
#         MessageModel.objects.create(
#             message=message, sender=employee, chat=conversation,
#         )

#     async def websocket_receive(self, event=None):
#         query_dict = json.loads(event.get('text', {}))
#         if query_dict.__len__() > 0:
#             token = query_dict.get('token')
#             if token is not None:
#                 user = await self.returnUser(token)
#                 if user != AnonymousUser():
#                     query_type = query_dict.get('queryType')
#                     if query_type == "get_messages":
#                         latest_messages = await self.getLatestMessages()
#                         await self.send({
#                             "type": "websocket.send",
#                             "text": latest_messages,
#                         })
#                     else:
#                         message = query_dict.get('content')
#                         employee = await UserModel.objects.aget(user_id__id=user.id)
#                         conversation = await ChatModel.objects.aget(chat_id=self.chat_id)
#                         await self.save_message(message, employee, conversation)
#                         # await self.send({
#                         #     "type": "websocket.send",
#                         #     "text": "message",
#                         #     "sender": user.id
#                         # })

#                 else:
#                     raise StopConsumer()
#             else:
#                 raise StopConsumer()

#     async def websocket_disconnect(self, close_code):
#         await (self.channel_layer.group_discard)(
#             self.chat_id, self.channel_name
#         )
#         raise StopConsumer()


from channels.generic.websocket import AsyncWebsocketConsumer

class TestConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        print("hi")  # Prints "hi" to your server console
        await self.accept()
