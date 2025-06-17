from rest_framework import serializers
from user_app.models import MainCategoryModel, SubCategoryModel

class SubCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = SubCategoryModel
        fields = ['id', 'name']

class MainCategorySerializer(serializers.ModelSerializer):
    subcategories = SubCategorySerializer(many=True, read_only=True)

    class Meta:
        model = MainCategoryModel
        fields = ['id', 'name', 'subcategories']