# category_app/views.py
from rest_framework import generics
from user_app.models import MainCategoryModel, SubCategoryModel
from user_app.Serializer.CategorySerializer import MainCategoryWithSubSerializer, SubCategorySerializer

class MainCategoryListAPIView(generics.ListAPIView):
    queryset = MainCategoryModel.objects.prefetch_related('subcategories').all()
    serializer_class = MainCategoryWithSubSerializer

class SubCategoryListAPIView(generics.ListAPIView):
    queryset = SubCategoryModel.objects.select_related('main_category').all()
    serializer_class = SubCategorySerializer
