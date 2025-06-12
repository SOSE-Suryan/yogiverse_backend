from django.shortcuts import render
from user_app.models import *
from rest_framework.views import APIView
from user_app.Serializer.UserSerializer import UserSerializer,ProfileSerializer,VendorProfileSerializer
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction
import ast


# Create your views here.

class VendorRegisterView(APIView):
    

    def post(self, request, *args, **kwargs):
        try:
            role = request.data.get('role')
            # with transaction.atomic():
            user_serializer = UserSerializer(data=request.data)
            if not user_serializer.is_valid():
                return Response(user_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            user = user_serializer.save()

            profile_data = {
                'user': user.id,
                'bio': request.data.get('bio'),
                'phone_no':request.data.get('phone_no'),
                'profile_picture': request.FILES.get('profile_picture'),
                'profile_link': request.data.get('profile_link')
                
            }
            profile_serializer = ProfileSerializer(data=profile_data)
            
            if profile_serializer.is_valid():
                profile_serializer.save()
                # profile = profile_serializer.save(user=user)
            if role == 'vendor':
                    # Parse lists if needed
                try:
                    main_categories = ast.literal_eval(request.data.get('main_categories', '[]'))
                    subcategories = ast.literal_eval(request.data.get('subcategories', '[]'))
                except:
                    main_categories = []
                    subcategories = []

                vendor_profile_data = {
                    'user': user,
                    'business_name': request.data.get('business_name'),
                    'main_categories': main_categories,
                    'subcategories': subcategories,
                    # 'pan_number': request.data.get('pan_number'),
                    # 'aadhar_number': request.data.get('aadhar_number'),
                    # 'gst_number': request.data.get('gst_number'),
                    # 'achievement_awards': request.data.get('achievement_awards'),
                    # 'business_type': request.data.get('business_type'),
                    # 'business_presence': request.data.get('business_presence'),
                    'description': request.data.get('description'),
                    # 'perma_link': request.data.get('perma_link'),
                    # 'store_owner': request.data.get('store_owner'),
                    'status': request.data.get('status'),
                    # 'vendor_status': request.data.get('vendor_status'),
                    'logo': request.FILES.get('logo'),
                    # 'pan_document': request.FILES.get('pan_document'),
                    # 'aadhar_document': request.FILES.get('aadhar_document'),
                    # 'gst_document': request.FILES.get('gst_document'),
                    # 'company_registration': request.FILES.get('company_registration'),
                    # 'msme_certificate': request.FILES.get('msme_certificate')
                }
                vendor_profile_serializer = VendorProfileSerializer(data=vendor_profile_data)
                if not vendor_profile_serializer.is_valid():
                    transaction.set_rollback(True)
                    return Response(vendor_profile_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
                vendor_profile_serializer.save(user=user)
            return Response({'status': True,'message': 'Registration successful!'}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({'status': False, 'message': 'Registration failed!', 'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
