from rest_framework import serializers
from user_app.models import UserModel,ProfileModel,VendorProfileModel,MainCategoryModel,SubCategoryModel,ProfileExternalLinkModel
from helper_app.models import CountryModel, StatesModel, CitiesModel

class ProfileExternalLinkSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProfileExternalLinkModel
        fields = ['url', 'title']

class ProfileSerializer(serializers.ModelSerializer):
    username = serializers.SerializerMethodField()
    email = serializers.SerializerMethodField()
    first_name = serializers.CharField(source='user.first_name', required=False)
    last_name = serializers.CharField(source='user.last_name', required=False)
    email = serializers.EmailField(source='user.email', required=False)
    phone_no = serializers.CharField(source='user.phone_no', required=False)
    username = serializers.CharField(source='user.username', required=False)
    country = serializers.PrimaryKeyRelatedField(source='user.country', queryset=CountryModel.objects.all(), required=False)
    state = serializers.PrimaryKeyRelatedField(source='user.state', queryset=StatesModel.objects.all(), required=False)
    city = serializers.PrimaryKeyRelatedField(source='user.city', queryset=CitiesModel.objects.all(), required=False)
    external_links = ProfileExternalLinkSerializer(many=True, read_only=True)

    def get_username(self, obj):
        return obj.user.username if obj.user else None
    
    def get_email(self, obj):
        return obj.user.email if obj.user else None
    
    class Meta:
        model = ProfileModel
        
        fields = [
            'id', 'bio',
            'first_name', 'last_name', 'email', 'phone_no', 'username','user',
            'profile_picture', 'profile_link', 'external_links',
            'country', 'state', 'city'
        ]
        
    def update(self, instance, validated_data):
        # Pop user data to update separately
        user_data = validated_data.pop('user', {})
        for attr, value in user_data.items():
            setattr(instance.user, attr, value)
        instance.user.save()

        # Update remaining profile fields
        return super().update(instance, validated_data)
        # fields = ['email','user','username','bio', 'phone_no','profile_picture', 'profile_link','external_links']


class VendorProfileSerializer(serializers.ModelSerializer):
    # main_categories = serializers.PrimaryKeyRelatedField(
    #     queryset=MainCategoryModel.objects.all(),many=True,required=False)
    # subcategories = serializers.PrimaryKeyRelatedField(
    #     queryset=SubCategoryModel.objects.all(),many=True,required=False)
    pan_document = serializers.FileField(required=False, allow_null=True)
    aadhar_document =serializers.FileField(required=False, allow_null=True)
    gst_document =serializers.FileField(required=False, allow_null=True)
    company_registration =serializers.FileField(required=False, allow_null=True)
    msme_certificate =serializers.FileField(required=False, allow_null=True)
        
    main_categories = serializers.SerializerMethodField()
    subcategories = serializers.SerializerMethodField()
    
    class Meta:
        model = VendorProfileModel
        exclude = ['user']

    def get_main_categories(self, obj):
        return list(obj.main_categories.values('id', 'name'))

    def get_subcategories(self, obj):
        return [
            {
                "id": sub.id,
                "name": sub.name,
                "main_category": {
                    "id": sub.main_category_id,
                    "name": sub.main_category.name
                }
            }
            for sub in obj.subcategories.select_related('main_category').all()
        ]
        
    
   

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
          
class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    role = serializers.ChoiceField(choices=UserModel.ROLE_CHOICES)

    class Meta:
        model = UserModel
        fields = [
            'id', 'email', 'username', 'password',
            'first_name', 'last_name', 'role',
            'phone_no', 'country', 'state', 'city'
        ]
        
    def create(self, validated_data):
        return UserModel.objects.create_user(**validated_data)
    
    