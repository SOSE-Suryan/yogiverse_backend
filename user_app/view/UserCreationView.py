from django.shortcuts import render
from user_app.models import *
from rest_framework.views import APIView
from user_app.Serializer.UserSerializer import UserSerializer,ProfileSerializer,VendorProfileSerializer,VendorProfileSlimSerializer
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction
import ast
from post_app.models import Post,Reel
from follower_app.models import Follower
from post_app.Serializer.PostSerializer import PostSerializer
from post_app.Serializer.ReelSerializer import ReelSerializer
from follower_app.serializers import FollowerSerializer
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
                    vendor_data = VendorProfileSerializer(vendor_profile).data
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
                    profile = ProfileModel.objects.get(user=id)
                    serializer = ProfileSerializer(profile, data=request.data, partial=True)

                    if not serializer.is_valid():
                        return Response({'status': False, 'message': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

                    serializer.save()

                    links_data = request.data.get('external_links', [])
                    existing_links_qs = ProfileExternalLinkModel.objects.filter(profile=profile)
                    existing_links_dict = {link.id: link for link in existing_links_qs}

                    received_ids = []

                    for link_data in links_data:
                        link_id = link_data.get('id')
                        if link_id and link_id in existing_links_dict:
                            # Update
                            link = existing_links_dict[link_id]
                            link.url = link_data['url']
                            link.title = link_data.get('title', '')
                            link.save()
                            received_ids.append(link_id)
                        else:
                            # Create new
                            new_link = ProfileExternalLinkModel.objects.create(
                                profile=profile,
                                url=link_data['url'],
                                title=link_data.get('title', '')
                            )
                            received_ids.append(new_link.id)

                    # Delete removed links
                    for link in existing_links_qs:
                        if link.id not in received_ids:
                            link.delete()

                    if request.user.role == 'vendor':
                        vendor_data = request.data.get('vendor_profile', None)
                        if vendor_data:
                            try:
                                vendor_profile = VendorProfileModel.objects.get(user=request.user)
                                vendor_serializer = VendorProfileSerializer(vendor_profile, data=vendor_data, partial=True)
                                if vendor_serializer.is_valid():
                                    vendor_serializer.save()
                                else:
                                    return Response({'status': False, 'message': vendor_serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
                            except VendorProfileModel.DoesNotExist:
                                return Response({'status': False, 'message': "Vendor profile not found"}, status=status.HTTP_404_NOT_FOUND)

                    
                    updated_profile = ProfileSerializer(profile).data
                    if request.user.role == 'vendor':
                        vendor_profile = VendorProfileModel.objects.get(user=request.user)
                        updated_profile = {
                            'profile': updated_profile,
                            'vendor_profile': VendorProfileSerializer(vendor_profile).data
                        }

                    return Response({'status': True, 'data': updated_profile, 'message': 'Profile updated successfully!'}, status=status.HTTP_200_OK)

                except Exception as e:
                    return Response({'status': False, 'message': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            else:
                return Response({"status": False, 'message': "Please select the Id you want to update"}, status=status.HTTP_400_BAD_REQUEST)
            
        else:
            return Response({'status': False, 'message': "Login is required"}, status=status.HTTP_401_UNAUTHORIZED)
        
        
class UserProfileView(APIView):
    
    def get(self,request,id=None):
        if id is not None:
            try:
                user= UserModel.objects.get(id=id)
                # profile = profile.profile  # assuming OneToOneField

                # Serialize profile
                profile_serializer = ProfileSerializer(user.profile)
                # Serialize vendor profile if user is a vendor
                if user.role == 'vendor':
                    vendor_profile = VendorProfileModel.objects.get(user=user)
                    vendor_profile_serializer = VendorProfileSlimSerializer(vendor_profile)
                else:
                    vendor_profile_serializer = None
                # Get posts and reels
                posts = Post.objects.filter(user=user)
                reels = Reel.objects.filter(user=user)

                posts_serializer = PostSerializer(posts, many=True)
                reels_serializer = ReelSerializer(reels, many=True)

                # Get followers/following counts
                followers_count = user.followers.count() if hasattr(user, 'followers') else 0
                following_count = user.following.count() if hasattr(user, 'following') else 0
                post_reels_count = posts.count() + reels.count()
                # post_reels_count = reels.count() if hasattr(user, 'reels') else 0
                
                if request.user.is_authenticated:
                    # Check if the authenticated user is following the profile user
                    following_relationship = Follower.objects.filter(
                        follower=request.user, 
                        following=user
                    ).first()
                    
                    # Check if the profile user is following the authenticated user
                    followed_by_relationship = Follower.objects.filter(
                        follower=user, 
                        following=request.user
                    ).first()
                    
                    is_following = following_relationship is not None
                    is_followed_by = followed_by_relationship is not None
                    
                    # Get follow status if following
                    follow_status = following_relationship.status if following_relationship else None
                else:
                    is_following = False
                    is_followed_by = False
                    follow_status = None


                return Response({
                    'status': True,
                    'message': 'Profile data fetched successfully!',
                    'data': {
                        'post_reels_count': post_reels_count,
                        'vendor_profile': vendor_profile_serializer.data if vendor_profile_serializer else None,
                        'role': user.role,
                        'profile': profile_serializer.data,
                        'posts': posts_serializer.data,
                        'reels': reels_serializer.data,
                        'followers_count': followers_count,
                        'following_count': following_count,
                        'is_following': is_following,
                        'is_followed_by': is_followed_by,
                        'follow_status': follow_status,
                    }
                }, status=status.HTTP_200_OK)
                
            except ProfileModel.DoesNotExist:
                return Response({'status': False, 'message': 'Vendor Profile not found!'}, status=status.HTTP_404_NOT_FOUND)
        else:
            return Response({'status': False, 'message': 'Please provide a valid ID.'}, status=status.HTTP_400_BAD_REQUEST)
    
    