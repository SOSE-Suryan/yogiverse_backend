from rest_framework.response import Response
from rest_framework.views import APIView
from user_app.models import *
from django.db.models import Q
from user_app.Serializer.CategorySerializer import *
from rest_framework import status
from user_app.paginations import DefaultPaginationClass


class MainSubCategoryAPI(APIView, DefaultPaginationClass):
    def get(self, request, pk=None):
        if pk:
            category = MainCategoryModel.objects.prefetch_related('subcategories').get(pk=pk)
            serializer = MainCategoryWithSubSerializer(category)
            return Response({
                "status": True,
                "data": serializer.data,
                "message": "Main category displayed"
            }, status=status.HTTP_200_OK)

        row_per_page = request.GET.get('row_per_page')
        if row_per_page:
            DefaultPaginationClass.page_size = row_per_page

        filter_search = request.GET.get('filter_search')
        if filter_search:
            categories = MainCategoryModel.objects.filter(name__icontains=filter_search).prefetch_related('subcategories')
            serializer = MainCategoryWithSubSerializer(categories, many=True)
            return Response({
                "status": True,
                "data": serializer.data,
                "message": "Filtered categories displayed"
            }, status=status.HTTP_200_OK)

        search_record = request.GET.get('search_record')
        if search_record:
            search_terms = search_record.split(',')
            search_query = Q()
            for term in search_terms:
                search_query |= Q(name__icontains=term)
            categories = MainCategoryModel.objects.filter(search_query).prefetch_related('subcategories')
            paginated = self.paginate_queryset(categories, request, view=self)
            serializer = MainCategoryWithSubSerializer(paginated, many=True)
            paginated_response = self.get_paginated_response(serializer.data).data
            return Response({
                "status": True,
                "data": serializer.data,
                "total_pages": paginated_response.get("total_pages"),
                "count": paginated_response.get("count"),
                "message": "Categories successfully displayed"
            }, status=status.HTTP_200_OK)

        categories = MainCategoryModel.objects.prefetch_related('subcategories').all()
        paginated = self.paginate_queryset(categories, request, view=self)
        serializer = MainCategoryWithSubSerializer(paginated, many=True)
        paginated_response = self.get_paginated_response(serializer.data).data
        return Response({
            "status": True,
            "data": serializer.data,
            "total_pages": paginated_response.get("total_pages"),
            "count": paginated_response.get("count"),
            "message": "Main categories successfully displayed"
        }, status=status.HTTP_200_OK)


