# yourapp/utils/mentions.py
import re
from django.contrib.contenttypes.models import ContentType
from user_app.models import UserModel
from post_app.models import MentionModel
from follower_app.models import FirebaseNotification
from firebase_admin import messaging
from follower_app.firebase_config import initialize_firebase, get_user_fcm_tokens
import time


def get_caption_and_media(instance):
    # Caption (works for all)
    caption = getattr(instance, 'caption', '')

    # Media
    # Post: related manager
    if hasattr(instance, 'media') and hasattr(instance.media, 'all') and instance.media.exists():
        media = [m.media_file.url for m in instance.media.all()]
    # Reel: video_file field
    elif hasattr(instance, 'video_file') and instance.video_file:
        media = [instance.video_file.url]
    # Story: media_file field
    elif hasattr(instance, 'media_file') and instance.media_file:
        media = [instance.media_file.url]
    else:
        media = []
    return caption, media



def save_mentions(creator, mentions, instance):
        content_type = ContentType.objects.get_for_model(instance)
        existing_mentions = set(MentionModel.objects.filter(content_type=content_type,
                                                            object_id=instance.id).values_list('mentioned_user_id', flat=True))
        # Prepare the new set from request
        new_mentions = set(mentions)
        
        # Find which users to add and remove
        to_add = new_mentions - existing_mentions
        to_remove = existing_mentions - new_mentions

        # Remove mentions no longer needed
        if to_remove:
            MentionModel.objects.filter(content_type=content_type,object_id=instance.id,mentioned_user_id__in=to_remove).delete()
        
        # Add new mentions
        for user_id in to_add:
            try:
                mentioned_user = UserModel.objects.get(id=user_id)
                if mentioned_user != creator:
                    MentionModel.objects.create(creator=creator,mentioned_user=mentioned_user,content_type=content_type,
                                                object_id=instance.id
                                                )
                    caption, media = get_caption_and_media(instance)
                    notification = FirebaseNotification.objects.create(
                    user=mentioned_user,
                    title='You were mentioned!',
                    body=f'@{creator.username} mentioned you in a {content_type.model}.',
                    data={
                        'type': 'mention',
                        'actor_id': str(creator.id),
                        'actor_name': creator.username,
                        'content_type': content_type.model,
                        'object_id': str(instance.id),
                        'caption':str(instance.caption),
                        'caption': caption,
                        'media': media,
                        # 'media':[m.media_file.url for m in instance.media.all()] if hasattr(instance, 'media') else [],
                    },
                    notification_type='mention',
                    sender=creator,
                    image_url=None,
                    action_url=None
                )

                # 3. SEND PUSH (if needed)
                try:
                    initialize_firebase()
                    tokens = get_user_fcm_tokens(mentioned_user)
                    if tokens:
                        for token in tokens:
                            try:
                                message = messaging.Message(
                                    notification=messaging.Notification(
                                        title='You were mentioned!',
                                        body=f'{creator.username} mentioned you in a {content_type.model}.',
                                        image=creator.profile.profile_picture.url if hasattr(creator, 'profile') and creator.profile.profile_picture else None
                                    ),
                                    data={
                                        'type': 'mention',
                                        'actor_id': str(creator.id),
                                        'actor_name': creator.username,
                                        'notification_id': str(notification.id),
                                        'object_id': str(instance.id),
                                        'content_type': content_type.model,
                                        'timestamp': str(int(time.time()))
                                    },
                                    token=token
                                )
                                messaging.send(message)
                            except Exception as e:
                                print(f"Error sending mention notification to token {token}: {str(e)}")
                except Exception as e:
                    print(f"Firebase send error: {str(e)}")
            except UserModel.DoesNotExist:
                continue
