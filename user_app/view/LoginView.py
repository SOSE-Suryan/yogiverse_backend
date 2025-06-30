# from rest_framework.generics import UpdateAPIView
# from rest_framework.response import Response
# from rest_framework import status
# from datetime import datetime
# from user_app.models import ProfileModel,UserModel
# from random import randint
# from Serializer.ContactSerializer import CustomerSendOtpSerializer
# from datetime import datetime
# from django.utils import timezone

# # from helper_app.Sms.sms_service import MSG91Service2

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import authenticate,logout
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.models import User
from rest_framework.permissions import IsAuthenticated

from user_app.models import VendorProfileModel

# class SendOtp(UpdateAPIView):
#     http_method_names = ['post']
#     serializer_class = CustomerSendOtpSerializer
    
#     def get_random_number(self):
#         #length of number of random.
#         res = randint(100000,999999)
#         return res

#     def post(self, request, *args, **kwargs):
#         try:
#             mobile_no = request.data.get('mobile_no', None)
#             if not mobile_no:
#                 return Response({'status': False, 'message': 'Please enter your mobile number.'}, status=status.HTTP_400_BAD_REQUEST)
            
#             profile = ProfileModel.objects.filter(mobile_no=mobile_no).first()
#             if not profile.user.is_active:
#                     return Response({'status': False, 'message': 'Your account has been deactivated!'}, status=status.HTTP_400_BAD_REQUEST)
                
#             otp = self.get_random_number()
#             otp_requested_at = datetime.now()
            
#             try:

#                 msg_service = MSG91Service2(authkey='351148ALYt1r4ponc5ff55ba1P1')
                
#                 online_template_id = '6708c95cd6fc054d1f010bd2'

#                 customer_mobile = str(mobile_no)
                
#                 # Send the SMS
#                 response = msg_service.send_message(
#                     template_id=online_template_id,
#                     mobiles=customer_mobile,
#                     var1=otp
#                 )                
#                 print(f"SMS Response (Login OTP): {response}")

#             except Exception as e:
#                 print(f"An error occurred while sending SMS: {e}")
#                 pass

#             if profile:
#                 data = {
#                 'otp': otp,
#                 'otp_requested_at': otp_requested_at
#             }
#                 serializer = CustomerSendOtpSerializer(instance=profile, data=data)
#                 serializer.is_valid(raise_exception=True)

#                 serializer.save(**data)

#                 data = serializer.data
#                 data['otp'] = 111111  # For security reasons, we don't want to send the OTP back to the response

#                 return Response({'status': True, 'data': data, 'message': 'OTP successfully Sent!'}, status=status.HTTP_200_OK)
        
                
#         except Exception as e:
#             return Response({
#                 'status': False,
#                 'message': str(e)
#             }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        
# class VerifyOtp(UpdateAPIView):
#     http_method_names = ['post']

#     def post(self, request, *args, **kwargs):
#         try:
#             user = None
#             mobile_no = request.data.get('mobile_no', None) 
#             if not mobile_no:
#                 return Response({'status': False, 'message': 'Please enter your mobile number.'}, status=status.HTTP_400_BAD_REQUEST)
            
#             otp = request.data.get('otp', None)
#             if not otp:
#                 return Response({'status': False, 'message': 'Please enter the OTP.'}, status=status.HTTP_400_BAD_REQUEST)
            
#             profile = ProfileModel.objects.filter(mobile_no=mobile_no, otp=otp).first()
            
#             if profile:
                
#                 if profile and profile.otp_requested_at is not None:
#                     current_time = timezone.now()
#                     time_diff = current_time - profile.otp_requested_at
#                     if time_diff.total_seconds() > 300:
#                         return Response({'status': False, 'message': 'OTP has expired. Please request a new one.'}, status=status.HTTP_400_BAD_REQUEST)
#                     user = profile.user

#                     profile.otp = None
#                     profile.otp_requested_at = None
#                     profile.save()
            
#         except Exception as e:
#             return Response({
#                 'status': False,
#                 'message': str(e)
#             }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)





# login with password........
class PasswordLoginView(APIView):
    
    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
    
        user = authenticate(username=username, password=password)
        if user is not None:
            if user.is_delete:
                return Response({'detail': 'Your account has been deleted'}, status=status.HTTP_401_UNAUTHORIZED)
            if user.role == 'vendor':
                is_vendor_verified = VendorProfileModel.objects.filter(user=user, vendor_status='verified').exists()
                if not is_vendor_verified:
                    return Response({'detail': 'Your Vendor account is not verified'}, status=status.HTTP_401_UNAUTHORIZED)
            refresh = RefreshToken.for_user(user)
            return Response({
                'refresh_token': str(refresh),
                'access_token': str(refresh.access_token),
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email               }
            })
        else:
            return Response({'detail': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)
        


class LogoutView(APIView):
    def post(self, request, format=None):
        if request.user.is_authenticated:
            logout(request)
            return Response({'status': True, 'message': 'User successfully logged out'}, status=status.HTTP_200_OK)
        else:
            return Response({'status': False, 'message': 'Login is required'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
