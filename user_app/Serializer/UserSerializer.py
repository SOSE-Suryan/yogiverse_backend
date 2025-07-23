from rest_framework import serializers
from user_app.models import UserModel,ProfileModel,VendorProfileModel,MainCategoryModel,SubCategoryModel,ProfileExternalLinkModel
from helper_app.models import CountryModel, StatesModel, CitiesModel
# from helper_app.serializer import CountriesSerializer, StateSerializer, CitiesSerializer
from post_app.models import CollectionItem,ContentType,Like

class ProfileExternalLinkSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProfileExternalLinkModel
        fields = ['url', 'title']

class ProfileSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(source='user.first_name', required=False)
    last_name = serializers.CharField(source='user.last_name', required=False)
    email = serializers.EmailField(source='user.email', required=False)
    phone_no = serializers.CharField(source='user.phone_no', required=False)
    username = serializers.CharField(source='user.username', required=False)
    country = serializers.PrimaryKeyRelatedField(source='user.country', queryset=CountryModel.objects.all(), required=False)
    state = serializers.PrimaryKeyRelatedField(source='user.state', queryset=StatesModel.objects.all(), required=False)
    city = serializers.PrimaryKeyRelatedField(source='user.city', queryset=CitiesModel.objects.all(), required=False)
    external_links = ProfileExternalLinkSerializer(many=True, read_only=True)
    profile_picture = serializers.ImageField(required=False, allow_null=True)
 
    # is_like = serializers.SerializerMethodField()
    # is_collection = serializers.SerializerMethodField()
    
    # def get_is_collection(self,obj):
    #     request = self.context.get('request')         
    #     user = getattr(request, 'user', None)
    #     if not user or not user.is_authenticated:
    #         return False

    #     content_type = ContentType.objects.get_for_model(obj._meta.model)

    #     is_collection= CollectionItem.objects.filter(
    #         # user=user,
    #         content_type=content_type,
    #         object_id=obj.id,
    #         is_collection=True
    #     ).exists()
        
    #     return is_collection
        
    # def get_is_like(self, obj):

    #     request = self.context.get('request')         
    #     user = getattr(request, 'user', None)
    #     print(user,'user prfileeeee')
    #     if not user or not user.is_authenticated:
    #         return False

    #     content_type = ContentType.objects.get_for_model(obj._meta.model)

    #     is_like= Like.objects.filter(
    #         user=user,
    #         content_type=content_type,
    #         object_id=obj.id,
    #         is_like=True
    #     ).exists()
        
    #     return is_like
    class Meta:
        model = ProfileModel
        
        fields = [
            'id', 'bio',
            'first_name', 'last_name', 'email', 'phone_no', 'username','user',
            'profile_picture', 'profile_link', 'external_links',
            'country', 'state', 'city'
        ]
        
    
        
    def to_representation(self, instance):
        rep = super().to_representation(instance)
        rep['country'] = instance.user.country.country_name if instance.user.country else None
        rep['state'] = instance.user.state.name if instance.user.state else None
        rep['city'] = instance.user.city.name if instance.user.city else None
        return rep
    
    def update(self, instance, validated_data):
        # Pop user data to update separately
        user_data = validated_data.pop('user', {})
        for attr, value in user_data.items():
            setattr(instance.user, attr, value)
        instance.user.save()

        return super().update(instance, validated_data)


class VendorProfileSerializer(serializers.ModelSerializer):
    main_categories = serializers.PrimaryKeyRelatedField(
        queryset=MainCategoryModel.objects.all(),many=True,required=False)
    subcategories = serializers.PrimaryKeyRelatedField(
        queryset=SubCategoryModel.objects.all(),many=True,required=False)
    pan_document = serializers.FileField(required=False, allow_null=True)
    aadhar_document =serializers.FileField(required=False, allow_null=True)
    gst_document =serializers.FileField(required=False, allow_null=True)
    company_registration =serializers.FileField(required=False, allow_null=True)
    msme_certificate =serializers.FileField(required=False, allow_null=True)
    logo = serializers.ImageField(required=False, allow_null=True)
    
    class Meta:
        model = VendorProfileModel
        exclude = ['user']
        
    def to_representation(self, instance):
        rep = super().to_representation(instance)
        rep['main_categories'] = list(instance.main_categories.values('id', 'name'))
        rep['subcategories'] = [
            {
                "id": sub.id,
                "name": sub.name,
                "main_category": {
                    "id": sub.main_category.id,
                    "name": sub.main_category.name
                }
            }
            for sub in instance.subcategories.select_related('main_category').all()
        ]
        return rep

        
    
   

class VendorProfileSlimSerializer(serializers.ModelSerializer):
    
    profile = ProfileSerializer(many=True, read_only=True) 
    class Meta:
        model = VendorProfileModel
        fields = [
            'profile',
            'business_name',
            'description',
            'status',
            'vendor_status',
            'logo',
            # 'vendor_banner'
        ]  
    
class UserMentionSerializer(serializers.ModelSerializer):
    profile_picture = serializers.SerializerMethodField()
    def get_profile_picture(self, obj):
        # Check if user has a profile and profile_picture
        profile = getattr(obj, 'profile', None)
        if profile and profile.profile_picture:
            return profile.profile_picture.url
        return None
    
    class Meta:
        model = UserModel
        fields = [
            'id',  'username', 
            'first_name', 'last_name', 'profile_picture']
       
class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    role = serializers.ChoiceField(choices=UserModel.ROLE_CHOICES)

    country = serializers.PrimaryKeyRelatedField(queryset=CountryModel.objects.all(), required=False, allow_null=True)
    state = serializers.PrimaryKeyRelatedField(queryset=StatesModel.objects.all(), required=False, allow_null=True)
    city = serializers.PrimaryKeyRelatedField(queryset=CitiesModel.objects.all(), required=False, allow_null=True)
    profile_picture = serializers.SerializerMethodField()
    
    def to_representation(self, instance):
        data = super().to_representation(instance)
        # Replace PKs with names in response
        data['country'] = instance.country.country_name if instance.country else None
        data['state'] = instance.state.name if instance.state else None
        data['city'] = instance.city.name if instance.city else None
        return data
    
    def get_profile_picture(self, obj):
        # Check if user has a profile and profile_picture
        profile = getattr(obj, 'profile', None)
        if profile and profile.profile_picture:
            return profile.profile_picture.url
        return None
    class Meta:
        model = UserModel
        fields = [
            'id', 'email', 'username', 'password',
            'first_name', 'last_name', 'role',
            'phone_no', 'country', 'state', 'city','profile_picture'
        ]
        
    def create(self, validated_data):
        return UserModel.objects.create_user(**validated_data)
    
    