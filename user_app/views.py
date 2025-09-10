from rest_framework.response import Response
from rest_framework.views import APIView
from user_app.models import *
from django.contrib.auth.hashers import make_password
from django.contrib.auth.hashers import check_password
from rest_framework import status
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from user_app.models import PasswordResetLinkModel
from django.conf import settings
from .get_connection import send_reset_email
from rest_framework.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta


class ResetPasswordSendLinkView(APIView):
    def post(self, request, format=None):
        try:
            email = request.data['email']
            get_user = UserModel.objects.get(email=email)
            new_reset_obj = PasswordResetLinkModel.objects.create(user=get_user)
            # http_referer = request.META.get('HTTP_REFERER', None)
            http_url ="https://yogiverse.in/" 
            new_reset_obj.url_link = f"{http_url}reset-password/{new_reset_obj.reset_uuid}"
            new_reset_obj.save()
            
            role = getattr(get_user, 'role', None)
            if role == 'vendor':
                from_email = 'vendor@yogiverse.in'
            elif role == 'user':
                 from_email = 'care@yogiverse.in'
            else:
                from_email = 'info@yogiverse.in'
                
            from_password = settings.EMAIL_HOST_PASSWORD
            # Render email content
            reset_link = new_reset_obj.url_link            
            subject = "Password Reset Request"
            # from_email = settings.EMAIL_HOST_USER
            to_email = [get_user.email]
            html_content = render_to_string('password_reset_email.html', {'reset_link': reset_link})
            
            send_reset_email(subject, html_content, from_email, from_password, to_email)
            # Send email
            # email = EmailMultiAlternatives(subject, html_content, from_email, to_email)
            # email.attach_alternative(html_content, "text/html")
            # email.send()
            
            return Response({'status': True, 'message': "A password reset link has been sent to your registered email!"}, status=status.HTTP_200_OK)
        except UserModel.DoesNotExist:
            return Response({'message': "Given email is not registered!"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'message': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ResetPasswordFormView(APIView):
    def post(self, request, reset_token=None, format=None):
        try:
            RESET_LINK_EXPIRY_MINUTES = 5

            fatch_user = PasswordResetLinkModel.objects.get(reset_uuid = reset_token)
            
            expiry_time = fatch_user.created_at + timedelta(minutes=RESET_LINK_EXPIRY_MINUTES)
            if timezone.now() > expiry_time:
                fatch_user.delete()  # Clean up the expired link
                return Response({'status': False, 'message': "Password reset link has expired. Generate a new one!"}, status=status.HTTP_400_BAD_REQUEST)
           
            new_password = request.data.get('new_password')
            confirm_password = request.data.get('confirm_password')
            if new_password == '' or new_password is None:
                return Response({'status': False,'message': "Enter new password!"}, status=status.HTTP_400_BAD_REQUEST)
            if confirm_password == '' or confirm_password is None:
                return Response({'status': False,'message': "Enter confirm password!"}, status=status.HTTP_400_BAD_REQUEST)
            if new_password == confirm_password:
                
                get_user = UserModel.objects.get(email=fatch_user.user.email)
                get_user.password = make_password(new_password)
                get_user.save()
                
                fatch_user.delete()
                return Response({'status': True, 'message': 'Password successfully reset. you can login now'}, status=status.HTTP_200_OK)
            else:
                return Response({'status': False, 'message': 'Password does not match'}, status=status.HTTP_400_BAD_REQUEST)
        
        except (PasswordResetLinkModel.DoesNotExist,ValidationError):
            return Response({'status': False,'message': f"Password rest link expired or invalid generate new one!"}, status=status.HTTP_400_BAD_REQUEST)
        
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
        
        
class DeleteAccountAPI(APIView):
    def post(self, request):
        if request.user.is_authenticated:
            user = UserModel.objects.get(email=request.user)
            if user.is_active:
                user.is_delete = True
                user.delete()
                return Response({"status": True, "message": "Your account has been successfully deleted!"})
            else:
                return Response({"status": False, "message": "Your account is already deleted!"})
        else:
            return Response({"status": False, "message": "Please login first!"})
        
