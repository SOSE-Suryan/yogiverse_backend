# category_app/views.py
from rest_framework import generics
from ..models import MainCategoryModel, SubCategoryModel
from user_app.Serializer.CategorySerializer import MainCategorySerializer, SubCategorySerializer

class MainCategoryListAPIView(generics.ListAPIView):
    queryset = MainCategoryModel.objects.prefetch_related('subcategories').all()
    serializer_class = MainCategorySerializer

class SubCategoryListAPIView(generics.ListAPIView):
    queryset = SubCategoryModel.objects.select_related('main_category').all()
    serializer_class = SubCategorySerializer
