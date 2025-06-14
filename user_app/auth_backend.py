from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model

UserModel = get_user_model()

class MultiFieldModelBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        user = None
        if username is None or password is None:
            return None
        try:
            # Try email
            user = UserModel.objects.get(email=username)
        except UserModel.DoesNotExist:
            try:
                # Try username
                user = UserModel.objects.get(username=username)
            except UserModel.DoesNotExist:
                try:
                    # Try phone number
                    user = UserModel.objects.get(phone_no=username)
                except UserModel.DoesNotExist:
                    return None
        if user and user.check_password(password):
            return user
        return None
