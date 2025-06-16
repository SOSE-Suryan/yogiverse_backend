import firebase_admin
from firebase_admin import credentials, messaging
from django.conf import settings
import os
import logging
from user_app.models import FCMTokenModel
import json

logger = logging.getLogger(__name__)

def initialize_firebase():
    """Initialize Firebase Admin SDK"""
    try:
        # Check if Firebase is already initialized
        app = firebase_admin.get_app()
        logger.info(f"Firebase already initialized with project ID: {app.project_id}")
        return app
    except ValueError:
        try:
            # Get the path to your Firebase service account key file
            service_account_path = os.path.join(settings.BASE_DIR, 'config', 'firebase-credentials.json')
            
            # Read the service account key file
            with open(service_account_path, 'r') as f:
                service_account_info = json.load(f)
            
            # Log project details for verification
            project_id = service_account_info.get('project_id')
            client_email = service_account_info.get('client_email')
            logger.info(f"Initializing Firebase with project ID: {project_id}")
            logger.info(f"Client email: {client_email}")
            
            # Initialize Firebase with your credentials
            cred = credentials.Certificate(service_account_info)
            app = firebase_admin.initialize_app(cred, {
                'projectId': project_id,
                'storageBucket': f"{project_id}.appspot.com"
            })
            logger.info(f"Firebase initialized successfully with project ID: {app.project_id}")
            return app
        except Exception as e:
            logger.error(f"Error initializing Firebase: {str(e)}")
            raise

def validate_token(token):
    """Validate a single FCM token"""
    try:
        # Initialize Firebase
        app = initialize_firebase()
        
        # Try to send a test message
        message = messaging.Message(
            notification=messaging.Notification(
                title='Token Validation',
                body='Validating your device token'
            ),
            token=token
        )
        
        # Send the message
        response = messaging.send(message)
        logger.info(f"Token validation successful: {response}")
        return True
        
    except Exception as e:
        error_message = str(e)
        logger.error(f"Token validation failed: {error_message}")
        
        if "Requested entity was not found" in error_message:
            logger.error("Token is not registered with Firebase")
            return False
        elif "SenderId mismatch" in error_message:
            logger.error("Token is from a different Firebase project")
            return False
        elif "Invalid registration token" in error_message:
            logger.error("Token is invalid or malformed")
            return False
        else:
            logger.error(f"Unknown error: {error_message}")
            return False

def get_user_fcm_tokens(user):
    """Get all valid FCM tokens for a user"""
    try:
        # Get all tokens for the user
        tokens = list(FCMTokenModel.objects.filter(user=user).values_list('token', flat=True))
        logger.info(f"Found {len(tokens)} tokens for user {user.id}")
        
        # Validate each token
        valid_tokens = []
        for token in tokens:
            if validate_token(token):
                valid_tokens.append(token)
            else:
                # Remove invalid token
                FCMTokenModel.objects.filter(token=token).delete()
                logger.info(f"Removed invalid token: {token[:20]}...")
        
        return valid_tokens
    except Exception as e:
        logger.error(f"Error getting FCM tokens for user {user.id}: {str(e)}")
        return []

def send_notification(user, title, body, data=None):
    """Send a simple notification to all devices of a user"""
    try:
        # Ensure Firebase is initialized
        app = initialize_firebase()
        logger.info(f"Using Firebase project ID: {app.project_id}")
        
        # Get all valid FCM tokens for the user
        tokens = get_user_fcm_tokens(user)
        
        if not tokens:
            logger.warning(f"No valid FCM tokens found for user {user.username}")
            return None
        
        success_count = 0
        failure_count = 0
        
        # Send individual messages to each token
        for token in tokens:
            try:
                # Create a simple message with web push configuration
                message = messaging.Message(
                    notification=messaging.Notification(
                        title=title,
                        body=body
                    ),
                    token=token,
                    webpush=messaging.WebpushConfig(
                        headers={
                            'Urgency': 'high'
                        },
                        notification=messaging.WebpushNotification(
                            title=title,
                            body=body,
                            icon='/static/images/logo.png',
                            badge='/static/images/badge.png'
                        )
                    )
                )
                
                # Send the message
                response = messaging.send(message)
                success_count += 1
                logger.info(f"Successfully sent notification to token: {token[:20]}...")
                
            except Exception as e:
                failure_count += 1
                error_message = str(e)
                logger.error(f"Failed to send notification to token {token[:20]}...: {error_message}")
                
                # Remove invalid token
                if "Requested entity was not found" in error_message:
                    FCMTokenModel.objects.filter(token=token).delete()
                    logger.info(f"Removed invalid token: {token[:20]}...")
        
        logger.info(f"Notification sending complete. Success: {success_count}, Failures: {failure_count}")
        return {'success_count': success_count, 'failure_count': failure_count}
        
    except Exception as e:
        logger.error(f"Error sending notification: {str(e)}")
        return None

def send_multicast_notification(users, title, body, data=None):
    """Send a notification to multiple users"""
    try:
        # Ensure Firebase is initialized
        initialize_firebase()
        
        # Get all FCM tokens for all users
        all_tokens = []
        for user in users:
            all_tokens.extend(get_user_fcm_tokens(user))
        
        if not all_tokens:
            logger.warning("No FCM tokens found for any users")
            return None
        
        success_count = 0
        failure_count = 0
        
        # Convert data values to strings if they aren't already
        if data:
            data = {k: str(v) for k, v in data.items()}
        
        # Send individual messages to each token
        for token in all_tokens:
            try:
                # Create the message with web push configuration
                message = messaging.Message(
                    notification=messaging.Notification(
                        title=title,
                        body=body
                    ),
                    data=data or {},
                    token=token,
                    webpush=messaging.WebpushConfig(
                        notification=messaging.WebpushNotification(
                            title=title,
                            body=body,
                            icon='/static/icons/icon-192x192.png',
                            badge='/static/icons/badge-72x72.png',
                            tag='notification',
                            require_interaction=True,
                            actions=[
                                {
                                    'action': 'open',
                                    'title': 'Open'
                                }
                            ]
                        ),
                        fcm_options=messaging.WebpushFCMOptions(
                            link='/'
                        )
                    )
                )
                
                # Send the message
                response = messaging.send(message)
                success_count += 1
                logger.info(f"Successfully sent notification to token: {token}")
                
            except Exception as e:
                failure_count += 1
                error_message = str(e)
                logger.error(f"Failed to send notification to token {token}: {error_message}")
                
                # Log specific error details
                if "Requested entity was not found" in error_message:
                    logger.error("Token is not registered with Firebase. This could be because:")
                    logger.error("1. The token is from a different Firebase project")
                    logger.error("2. The token has expired")
                    logger.error("3. The token was never properly registered")
                elif "SenderId mismatch" in error_message:
                    logger.error("Token is from a different Firebase project")
                elif "Invalid registration token" in error_message:
                    logger.error("Token is invalid or malformed")
        
        logger.info(f"Multicast notification sending complete. Success: {success_count}, Failures: {failure_count}")
        return {'success_count': success_count, 'failure_count': failure_count}
        
    except Exception as e:
        logger.error(f"Error sending multicast notification: {str(e)}")
        return None 