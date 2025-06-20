from rest_framework import serializers
from user_app.models import UserModel,ProfileModel,VendorProfileModel,MainCategoryModel,SubCategoryModel,ProfileExternalLinkModel
from helper_app.models import CountryModel, StatesModel, CitiesModel
from helper_app.serializer import CountriesSerializer, StateSerializer, CitiesSerializer

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
    profile_picture = serializers.ImageField(required=False, allow_null=True)
    
    
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
    main_categories = serializers.PrimaryKeyRelatedField(
        queryset=MainCategoryModel.objects.all(),many=True,required=False)
    subcategories = serializers.PrimaryKeyRelatedField(
        queryset=SubCategoryModel.objects.all(),many=True,required=False)
    pan_document = serializers.FileField(required=False, allow_null=True)
    aadhar_document =serializers.FileField(required=False, allow_null=True)
    gst_document =serializers.FileField(required=False, allow_null=True)
    company_registration =serializers.FileField(required=False, allow_null=True)
    msme_certificate =serializers.FileField(required=False, allow_null=True)
        
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
          
class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    role = serializers.ChoiceField(choices=UserModel.ROLE_CHOICES)

    country = serializers.SerializerMethodField()
    state = serializers.SerializerMethodField()
    city = serializers.SerializerMethodField()
    
    def get_country(self, obj):
        return obj.country.country_name if obj.country else None
    
    def get_state(self, obj):
        return obj.state.name if obj.state else None
    
    def get_city(self, obj):
        return obj.city.name if obj.city else None
    
    class Meta:
        model = UserModel
        fields = [
            'id', 'email', 'username', 'password',
            'first_name', 'last_name', 'role',
            'phone_no', 'country', 'state', 'city'
        ]
        
    def create(self, validated_data):
        return UserModel.objects.create_user(**validated_data)
    
    