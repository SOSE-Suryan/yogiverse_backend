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
import logging

# Configure logging
logger = logging.getLogger(__name__)

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
                logger.info(f"Fetching profile for user ID: {id}")

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

                # Get followers/following counts - only count approved relationships
                # user.followers = users who follow this user (following field in Follower model)
                # user.following = users this user follows (follower field in Follower model)
                followers_count = user.followers.filter(status='approved').count()
                following_count = user.following.filter(status='approved').count()
                post_reels_count = posts.count() + reels.count()
                
                logger.info(f"Followers count (approved): {followers_count}")
                logger.info(f"Following count (approved): {following_count}")
                
                # post_reels_count = reels.count() if hasattr(user, 'reels') else 0
                
                if request.user.is_authenticated:
                    logger.info(f"Authenticated user: {request.user.id} - {request.user.username}")
                    logger.info(f"Profile user: {user.id} - {user.username}")
                    
                    try:
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
                        
                        # Debug: Check all relationships for both users
                        all_following_relationships = Follower.objects.filter(follower=request.user)
                        all_followed_by_relationships = Follower.objects.filter(following=request.user)
                        
                        logger.info(f"All following relationships for {request.user.username}: {list(all_following_relationships.values('following__username', 'status'))}")
                        logger.info(f"All followed by relationships for {request.user.username}: {list(all_followed_by_relationships.values('follower__username', 'status'))}")
                        
                        # Debug: Check specific relationship
                        logger.info(f"Looking for relationship: {request.user.username} -> {user.username}")
                        logger.info(f"Following relationship object: {following_relationship}")
                        if following_relationship:
                            logger.info(f"Following relationship status: {following_relationship.status}")
                            logger.info(f"Following relationship ID: {following_relationship.id}")
                        
                        # Only consider as following if status is 'approved'
                        is_following = following_relationship is not None and following_relationship.status == 'approved'
                        is_followed_by = followed_by_relationship is not None and followed_by_relationship.status == 'approved'
                        
                        # Always return the actual status if relationship exists, otherwise None
                        if following_relationship:
                            follow_status = following_relationship.status
                            logger.info(f"Following relationship found with status: {follow_status}")
                        else:
                            follow_status = None
                            logger.info("No following relationship found")
                        
                        logger.info(f"Final follow_status value: {follow_status}")
                        logger.info(f"Final is_following value: {is_following}")
                        logger.info(f"Followed by relationship: {followed_by_relationship}")
                        logger.info(f"Is followed by: {is_followed_by}")
                        
                    except Exception as e:
                        logger.error(f"Error processing follow relationships: {str(e)}")
                        import traceback
                        logger.error(f"Traceback: {traceback.format_exc()}")
                        is_following = False
                        is_followed_by = False
                        follow_status = None
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
                        # Debug info - remove this after testing
                        'debug_info': {
                            'authenticated_user_id': request.user.id if request.user.is_authenticated else None,
                            'profile_user_id': user.id,
                            'follow_status_type': type(follow_status).__name__ if follow_status else 'None',
                            'follow_status_value': str(follow_status) if follow_status else None,
                        }
                    }
                }, status=status.HTTP_200_OK)
                
            except ProfileModel.DoesNotExist:
                logger.error(f"Profile not found for user ID: {id}")
                return Response({'status': False, 'message': 'Vendor Profile not found!'}, status=status.HTTP_404_NOT_FOUND)
            except Exception as e:
                logger.error(f"Error fetching profile for user ID {id}: {str(e)}")
                return Response({'status': False, 'message': 'An error occurred while fetching profile.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            logger.warning("UserProfileView called without ID parameter")
            return Response({'status': False, 'message': 'Please provide a valid ID.'}, status=status.HTTP_400_BAD_REQUEST)
    
    