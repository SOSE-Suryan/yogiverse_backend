from django.apps import AppConfig


class FollowerAppConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "follower_app"

    def ready(self):
        try:
            from .firebase_config import initialize_firebase
            initialize_firebase()
        except Exception as e:
            print(f"Error initializing Firebase: {str(e)}")
