from rest_framework import serializers
from user_app.models import UserModel,ProfileModel,VendorProfileModel,MainCategoryModel,SubCategoryModel


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProfileModel
        fields = ['user','bio', 'phone_no','profile_picture', 'profile_link']



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
        
class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    role = serializers.ChoiceField(choices=UserModel.ROLE_CHOICES)

    class Meta:
        model = UserModel
        fields = [
            'email', 'username', 'password',
            'first_name', 'last_name', 'role',
            'phone_no', 'country', 'state', 'city'
        ]
        
    def create(self, validated_data):
        return UserModel.objects.create_user(**validated_data)
    
    