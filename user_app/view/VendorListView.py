from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from user_app.models import UserModel,VendorProfileModel,ProfileModel,SubCategoryModel
from user_app.Serializer.UserSerializer import UserSerializer,ProfileSerializer,VendorProfileSerializer
from post_app.models import Post,Reel
from post_app.Serializer.PostSerializer import PostSerializer
from post_app.Serializer.ReelSerializer import ReelSerializer

class VendorListView(APIView):
    
    """
    API view to list all vendors.
    """
    def get(self, request, format=None):
        try:
            vendors = UserModel.objects.filter(role='vendor').select_related('profile').prefetch_related(
                'vendor_profile', 'vendor_profile__main_categories', 'vendor_profile__subcategories', 'followers', 'following'
            )

            # Get query parameters
            main_category_id = request.query_params.get('main_category')
            subcategory_id = request.query_params.get('subcategory')

            # Apply filters
            if main_category_id:
                try:
                    main_category_id = int(main_category_id)
                    vendors = vendors.filter(vendor_profile__main_categories__id=main_category_id)
                    
                    # If subcategory_id is provided, validate it belongs to the main_category
                    if subcategory_id:
                        try:
                            subcategory_id = int(subcategory_id)
                            
                            if not SubCategoryModel.objects.filter(id=subcategory_id, main_category__id=main_category_id).exists():
                                return Response({
                                    'status': False,
                                    'message': 'Subcategory does not belong to the provided main category.'
                                }, status=status.HTTP_400_BAD_REQUEST)
                            vendors = vendors.filter(vendor_profile__subcategories__id=subcategory_id)
                        except ValueError:
                            return Response({
                                'status': False,
                                'message': 'Invalid subcategory ID.'
                            }, status=status.HTTP_400_BAD_REQUEST)
                except ValueError:
                    return Response({
                        'status': False,
                        'message': 'Invalid main category ID.'
                    }, status=status.HTTP_400_BAD_REQUEST)                            
                
            vendor_list = []
            for vendor in vendors:
                user_serializer = UserSerializer(vendor)
                
                # Profile
                try:
                    profile_serializer = ProfileSerializer(vendor.profile)
                except ProfileModel.DoesNotExist:
                    profile_serializer = None

                # Vendor Profile
                try:
                    vendor_profile = VendorProfileModel.objects.get(user=vendor)
                    vendor_profile_serializer = VendorProfileSerializer(vendor_profile)
                    
                except VendorProfileModel.DoesNotExist:
                    vendor_profile_serializer = None

                # Get posts and reels
                posts = Post.objects.filter(user=vendor)
                reels = Reel.objects.filter(user=vendor)

                posts_serializer = PostSerializer(posts, many=True)
                reels_serializer = ReelSerializer(reels, many=True)

                # Get followers/following counts
                followers_count = vendor.followers.count() if hasattr(vendor, 'followers') else 0
                following_count = vendor.following.count() if hasattr(vendor, 'following') else 0
                post_reels_count = posts.count() + reels.count()

                vendor_list.append({
                        'post_reels_count': post_reels_count,
                        'user': user_serializer.data,
                        'vendor_profile': vendor_profile_serializer.data if vendor_profile_serializer else None,
                        # 'role': vendor.role,
                        'profile': profile_serializer.data,
                        'posts': posts_serializer.data,
                        'reels': reels_serializer.data,
                        'followers_count': followers_count,
                        'following_count': following_count,
                    
                })
                
            return Response({
                'status': True,
                'message': 'Vendor list fetched successfully!',
                'vendors': vendor_list
            }, status=status.HTTP_200_OK)
                
        except ProfileModel.DoesNotExist:
            return Response({'status': False, 'message': 'Vendor Profile not found!'}, status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            return Response({'status': False, 'message': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)