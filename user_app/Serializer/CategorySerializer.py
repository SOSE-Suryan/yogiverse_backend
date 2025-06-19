from rest_framework import serializers
from user_app.models import *

class SubCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = SubCategoryModel
        fields = ['id', 'name', 'main_category']

class MainCategoryWithSubSerializer(serializers.ModelSerializer):
    categories = serializers.IntegerField(source='id')
    category_name = serializers.CharField(source='name')
    sub_categories = SubCategorySerializer(source='subcategories', many=True)

    class Meta:
        model = MainCategoryModel
        fields = ['categories', 'category_name', 'sub_categories']