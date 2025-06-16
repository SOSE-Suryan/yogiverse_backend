from django.core.management.base import BaseCommand
from user_app.models import FCMTokenModel
from firebase_admin import messaging
from follower_app.firebase_config import initialize_firebase
import logging
import time

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Clears invalid FCM tokens from the database'

    def handle(self, *args, **options):
        try:
            # Initialize Firebase
            initialize_firebase()
            
            # Get all tokens
            tokens = FCMTokenModel.objects.all()
            total_tokens = tokens.count()
            invalid_tokens = 0
            
            self.stdout.write(f"Found {total_tokens} tokens to validate...")
            
            for token_model in tokens:
                try:
                    # Try to send a test message
                    message = messaging.Message(
                        notification=messaging.Notification(
                            title='Token Validation',
                            body='Validating your device token'
                        ),
                        data={
                            'type': 'validation',
                            'timestamp': str(int(time.time()))
                        },
                        token=token_model.token
                    )
                    
                    # Send the message
                    messaging.send(message)
                    self.stdout.write(self.style.SUCCESS(f"Token {token_model.token} is valid"))
                    
                except Exception as e:
                    error_message = str(e)
                    if any(error in error_message.lower() for error in ['senderid mismatch', 'not found', 'invalid', 'unregistered']):
                        token_model.delete()
                        invalid_tokens += 1
                        self.stdout.write(self.style.WARNING(f"Removed invalid token: {token_model.token}"))
            
            self.stdout.write(self.style.SUCCESS(f"Token cleanup complete. Removed {invalid_tokens} invalid tokens out of {total_tokens} total tokens."))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error clearing invalid tokens: {str(e)}")) 