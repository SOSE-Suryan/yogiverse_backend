from rest_framework.response import Response
from rest_framework.views import APIView
from user_app.models import UserModel
from django.contrib.auth.hashers import make_password
from django.contrib.auth.hashers import check_password
from rest_framework import status

from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from user_app.models import PasswordResetLinkModel
from django.conf import settings

class ResetPasswordSendLinkView(APIView):
    def post(self, request, format=None):
        try:
            email = request.data['email']
            get_user = UserModel.objects.get(email=email)
            new_reset_obj = PasswordResetLinkModel.objects.create(user=get_user)
            http_referer = request.META.get('HTTP_REFERER', None)
            new_reset_obj.url_link = f"{http_referer}reset-password/{new_reset_obj.reset_uuid}"
            print(new_reset_obj.url_link,"new_reset_obj.url_link")
            new_reset_obj.save()
            
            role = getattr(get_user, 'role', None)
            if role == 'vendor':
                from_email = settings.EMAIL_VENDOR
            elif role == 'user':
                from_email = settings.EMAIL_USER
            else:
                from_email = settings.EMAIL_HOST_USER
            # Render email content
            reset_link = new_reset_obj.url_link
            subject = "Password Reset Request"
            # from_email = settings.EMAIL_HOST_USER
            to_email = [get_user.email]
            html_content = render_to_string('password_reset_email.html', {'reset_link': reset_link})
            
            # Send email
            email = EmailMultiAlternatives(subject, html_content, from_email, to_email)
            email.attach_alternative(html_content, "text/html")
            email.send()
            
            return Response({'status': True, 'message': "A password reset link has been sent to your registered email!"}, status=status.HTTP_200_OK)
        except UserModel.DoesNotExist:
            return Response({'message': "Given email is not registered!"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'message': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class ChangePasswordView(APIView):
    def post(self, request, format=None):
        if request.user.is_authenticated:
            try:
                old_password = request.data['old_password']
                new_password = request.data['new_password']
                confirm_password = request.data['confirm_password']
                check_old_pass = request.user.check_password(old_password)
                # data = {}

                if check_old_pass:

                    if check_password(new_password, request.user.password):
                        return Response({'status': False, 'message': 'Password alredy you have !'}, status=status.HTTP_400_BAD_REQUEST)

                    if new_password == confirm_password:
                        request.user.password = make_password(new_password)
                        request.user.save()
                        # data['old_password'] = old_password
                        # data['new_password'] = new_password
                        # return Response({'status':True,'data':data,'message':'Password successfully changed'}, status=status.HTTP_200_OK)
                        return Response({'status': True, 'message': 'Password changed successfully!'}, status=status.HTTP_200_OK)
                    else:
                        return Response({'status': False, 'message': 'Passwords do not match'}, status=status.HTTP_400_BAD_REQUEST)

                else:
                    return Response({'status': False, 'message': 'Old Password is wrong'}, status=status.HTTP_400_BAD_REQUEST)
            except Exception as e:
                if str(e.args[0]) == 'old_password':
                    return Response({'old_password': "This field is required."}, status=status.HTTP_400_BAD_REQUEST)
                elif str(e.args[0]) == 'new_password':
                    return Response({'new_password': "This field is required."}, status=status.HTTP_400_BAD_REQUEST)
                return Response({'confirm_password': "This field is required."}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({'status': False, 'message': 'Login is required'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class DeactivateAccountAPI(APIView):
    def post(self, request):
        if request.user.is_authenticated:
            user = UserModel.objects.get(email=request.user)
            if user.is_active:
                user.is_active = False
                user.save()
                return Response({"status": True, "message": "Your account has been successfully deactivated!"})
            else:
                return Response({"status": False, "message": "Your account is already deactivated!"})
        else:
            return Response({"status": False, "message": "Please login first!"})