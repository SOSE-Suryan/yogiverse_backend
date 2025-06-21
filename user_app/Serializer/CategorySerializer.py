from rest_framework import serializers
from user_app.models import *

class SubCategorySerializer(serializers.ModelSerializer):
    sub_category_image = serializers.ImageField(allow_null=True, required=False)
    class Meta:
        model = SubCategoryModel
        fields = ['id', 'name', 'main_category','sub_category_image']

class MainCategoryWithSubSerializer(serializers.ModelSerializer):
    categories = serializers.IntegerField(source='id')
    category_name = serializers.CharField(source='name')
    main_category_image = serializers.ImageField( allow_null=True, required=False)
    sub_categories = SubCategorySerializer(source='subcategories', many=True)

    class Meta:
        model = MainCategoryModel
        fields = ['categories', 'category_name', 'sub_categories','main_category_image']
