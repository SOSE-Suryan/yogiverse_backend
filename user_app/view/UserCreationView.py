from django.shortcuts import render
from user_app.models import *
from rest_framework.views import APIView
from user_app.Serializer.UserSerializer import UserSerializer,ProfileSerializer,VendorProfileSerializer,VendorProfileSlimSerializer
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction
import ast


# Create your views here.

class VendorRegisterView(APIView):
    
    def post(self, request, *args, **kwargs):
        role = request.data.get('role')
        try:
            with transaction.atomic():
                user_serializer = UserSerializer(data=request.data)
                if not user_serializer.is_valid():
                    return Response({"status": False, "message": "User validation failed.", "errors": user_serializer.errors},status=status.HTTP_400_BAD_REQUEST)        
                user = user_serializer.save()
                
                profile_data = {
                    'user': user.id,
                    'bio': request.data.get('bio'),
                    'phone_no':request.data.get('phone_no'),
                    'profile_picture': request.FILES.get('profile_picture'),
                    'profile_link': f"https://yogiverse.in/profile/{user.username}"
                    
                }

                profile_serializer = ProfileSerializer(data=profile_data)

                if not profile_serializer.is_valid():
                            transaction.set_rollback(True)
                            return Response(
                                {"status": False, "message": "Profile validation failed.", "errors": profile_serializer.errors},
                                status=status.HTTP_400_BAD_REQUEST
                            )
                                
                profile_serializer.save()
                
                if role == 'vendor':
                        # Parse lists if needed
                    try:
                        main_categories = ast.literal_eval(request.data.get('main_categories', '[]'))
                        subcategories = ast.literal_eval(request.data.get('subcategories', '[]'))
                    except Exception as e:
                                transaction.set_rollback(True)
                                return Response(
                                    {"status": False, "message": f"Category parsing error: {str(e)}"},
                                    status=status.HTTP_400_BAD_REQUEST
                                )

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
                        return Response(
                                    {"status": False, "message": "Vendor profile validation failed.", "errors": vendor_profile_serializer.errors},
                                    status=status.HTTP_400_BAD_REQUEST
                                )
                    vendor_profile_serializer.save(user=user)
                return Response({'status': True,'message': 'Registration successful!'}, status=status.HTTP_200_OK)

        except Exception as e:
            # Log the exception for debugging (optional)
            import traceback
            traceback.print_exc()
            return Response(
                {"status": False, "message": "An unexpected error occurred.", "errors": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

class ProfileView(APIView):
    
    def get(self,request):
        
        try:
            profile = ProfileModel.objects.get(user=request.user)
            profile_data = ProfileSerializer(profile).data
            data = {'profile': profile_data}

            try:
                if request.user.role == 'vendor':
                    vendor_profile = VendorProfileModel.objects.get(user=request.user)
                    vendor_data = VendorProfileSlimSerializer(vendor_profile).data
                    data['vendor_profile'] = vendor_data
            except VendorProfileModel.DoesNotExist:
                data['vendor_profile'] = None
                
            return Response({'status': True,'data':data,'message': 'Profile Display Successfully!'}, status=status.HTTP_200_OK)
        except ProfileModel.DoesNotExist:
            return Response({'status': False, 'message': 'Profile not found!'}, status=status.HTTP_404_NOT_FOUND)
    
    def patch(self,request,id):
        if request.user.is_authenticated:

            if id is not None: 
                try:
                    get_profile = ProfileModel.objects.get(id=id)

                    serializer = ProfileSerializer(get_profile,data=request.data,partial=True)
                    if serializer.is_valid():
                        serializer.save()
                        links_data = request.data.get('external_links', [])
                        existing_links_qs = ProfileExternalLinkModel.objects.filter(profile=id)
                        for i, link_data in enumerate(links_data):
                            if i < existing_links_qs.count():
                                # UPDATE existing
                                link = existing_links_qs[i]
                                link.url = link_data['url']
                                link.title = link_data.get('title', '')
                                link.save()
                            else:
                                # CREATE new
                                ProfileExternalLinkModel.objects.create(
                                    profile=get_profile,
                                    url=link_data['url'],
                                    title=link_data.get('title', '')
                                )
                        # 2. Delete any extra old links
                        if existing_links_qs.count() > len(links_data):
                            # delete links from len(links_data) to end
                            for link in existing_links_qs[len(links_data):]:
                                link.delete()
                                
                        # if request.user.role == 'vendor':
                            
                        #     vendor_profile_data = request.data.get('vendor_profile', None)

                        #     vendor_profile = VendorProfileModel.objects.get(user=request.user)
                            
                        # Return updated profile
                        updated_profile = ProfileSerializer(get_profile)
                            
                    return Response({'status': True,'data':updated_profile.data,'message': 'Profile Update Successfully !'}, status=status.HTTP_200_OK)
                except Exception as e:
                    return Response({'status': False, 'message': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            else:
                return Response({"status": False, 'message': "Please select the Id you want to update"}, status=status.HTTP_400_BAD_REQUEST)
            
        else:
            return Response({'status': False, 'message': "Login is required"}, status=status.HTTP_401_UNAUTHORIZED)