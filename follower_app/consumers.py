import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import Follower
from django.contrib.auth import get_user_model
import logging

logger = logging.getLogger(__name__)
User = get_user_model()

class FollowCountConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"]
        if not self.user.is_authenticated:
            await self.close()
            return

        # Create unique group names for this user
        self.followers_group = f"followers_{self.user.id}"
        self.following_group = f"following_{self.user.id}"
        
        # Join room groups
        await self.channel_layer.group_add(
            self.followers_group,
            self.channel_name
        )
        await self.channel_layer.group_add(
            self.following_group,
            self.channel_name
        )
        
        await self.accept()
        
        # Send initial counts
        followers_count, following_count = await self.get_follow_counts()
        await self.send(text_data=json.dumps({
            'type': 'follow_counts',
            'followers_count': followers_count,
            'following_count': following_count
        }))
        
        logger.info(f"WebSocket connected for user {self.user.id}")

    async def disconnect(self, close_code):
        # Leave room groups
        await self.channel_layer.group_discard(
            self.followers_group,
            self.channel_name
        )
        await self.channel_layer.group_discard(
            self.following_group,
            self.channel_name
        )
        logger.info(f"WebSocket disconnected for user {self.user.id}")

    async def receive(self, text_data):
        # Handle any incoming messages if needed
        pass

    async def follow_count_update(self, event):
        """
        Send follow counts update to WebSocket
        """
        await self.send(text_data=json.dumps({
            'type': 'follow_counts',
            'followers_count': event['followers_count'],
            'following_count': event['following_count']
        }))

    @database_sync_to_async
    def get_follow_counts(self):
        """
        Get the counts of followers and following for the user
        """
        followers_count = Follower.objects.filter(
            following=self.user,
            status='approved'
        ).count()
        
        following_count = Follower.objects.filter(
            follower=self.user,
            status='approved'
        ).count()
        
        return followers_count, following_count 