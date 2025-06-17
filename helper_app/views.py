from django.shortcuts import render
from .models import CountryModel,StatesModel,CitiesModel
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from .serializer import CountriesSerializer,StateSerializer,CitiesSerializer,InquirySerializer
from rest_framework import status
from helper_app.paginations import DefaultPaginationClass
from django.db.models import Q

# Create your views here.
class CountriesAPI(APIView, DefaultPaginationClass):
    def get(self, request, pk=None,):
        id = pk
        if id is not None:
            country = CountryModel.objects.get(pk=id)
            serializer = CountriesSerializer(country)
            return Response({"status":True, "data":serializer.data, "message": "Country displayed"}, status=status.HTTP_200_OK)
        filter_contires = request.GET.get('filter_search')
        if filter_contires:
            countries_list = CountryModel.objects.filter(country_name__icontains=filter_contires)
            serializer = CountriesSerializer(countries_list, many = True)
            return Response({'status':True, 'data':serializer.data,'message':'Countries successfully displayed'},status=status.HTTP_200_OK)
        row_per_page = request.GET.get('row_per_page')
        if row_per_page:
            DefaultPaginationClass.page_size = row_per_page

        search_record = request.GET.get('search_record')
        if  search_record:
            search_terms = search_record.split(',')
            search_query = Q()
            for term in search_terms:
                search_query |= Q(country_name__icontains=term)
            # data = warehouses.filter(search_query)
            countries_list = CountryModel.objects.filter(search_query)
            paginated_countries = self.paginate_queryset(countries_list, request, view=self)
            serializer = CountriesSerializer(paginated_countries, many = True)
            paginated_response = self.get_paginated_response(serializer.data).data
            return Response({'status':True, 'data':serializer.data, 'total_pages': paginated_response.get('total_pages'), 'count': paginated_response.get('count'), 'message':'Countries successfully displayed'},status=status.HTTP_200_OK)
        countries_list = CountryModel.objects.all()
        paginated_countries = self.paginate_queryset(countries_list, request, view=self)
        serializer = CountriesSerializer(paginated_countries, many = True)
        paginated_response = self.get_paginated_response(serializer.data).data
        return Response({'status':True, 'data':serializer.data, 'total_pages': paginated_response.get('total_pages'), 'count': paginated_response.get('count'), 'message':'Countries successfully displayed'},status=status.HTTP_200_OK)
        
# States API   
class StatesAPI(APIView, DefaultPaginationClass):
    def get(self, request, pk=None):
        country_id = pk
        if country_id:
            states_list = StatesModel.objects.filter(country_id=country_id)
            serializer = StateSerializer(states_list, many = True)
            return Response({'status':True,'data':serializer.data,'message':'States successfully displayed'},status=status.HTTP_200_OK)
        row_per_page = request.GET.get('row_per_page')
        if row_per_page:
            DefaultPaginationClass.page_size = row_per_page
        
        filter_contires = request.GET.get('filter_search')
        if filter_contires:
            states_list = StatesModel.objects.filter(name__icontains=filter_contires)

            serializer = StateSerializer(states_list, many = True)
            return Response({'status':True, 'data':serializer.data,'message':'States successfully displayed'},status=status.HTTP_200_OK)
        
        search_record = request.GET.get('search_record')
        if search_record:
            states_list = StatesModel.objects.filter(name__icontains=search_record)
            paginated_states = self.paginate_queryset(states_list, request, view=self)
            serializer = StateSerializer(paginated_states, many = True)
            paginated_response = self.get_paginated_response(serializer.data).data
            return Response({'status':True,'data': serializer.data, 'total_pages': paginated_response.get('total_pages'), 'count': paginated_response.get('count'), 'message':'States successfully displayed'},status=status.HTTP_200_OK)
            
        states_list = StatesModel.objects.all()
        paginated_states = self.paginate_queryset(states_list, request, view=self)
        serializer = StateSerializer(paginated_states, many = True)
        paginated_response = self.get_paginated_response(serializer.data).data
        return Response({'status':True,'data': serializer.data, 'total_pages': paginated_response.get('total_pages'), 'count': paginated_response.get('count'), 'message':'States successfully displayed'},status=status.HTTP_200_OK)
        

# Cities API
class CitiesAPI(APIView, DefaultPaginationClass):
    def get(self, request, state_id=None):
        row_per_page = request.GET.get('row_per_page')
        search_record = request.GET.get('search_record')
        if row_per_page:
            DefaultPaginationClass.page_size = row_per_page


        if search_record:
            cities_list = CitiesModel.objects.filter(name__icontains=search_record)
            paginated_cities = self.paginate_queryset(cities_list, request, view=self)
            serializer = CitiesSerializer(paginated_cities, many = True)
            paginated_response = self.get_paginated_response(serializer.data).data
            return Response({'status':True,'data':serializer.data,'total_pages': paginated_response.get('total_pages'), 'count': paginated_response.get('count'),'message':'Cities successfully displayed'},status=status.HTTP_200_OK)
        
        if state_id:
            cities_list = CitiesModel.objects.filter(state_id=state_id)
            serializer = CitiesSerializer(cities_list, many = True)
            return Response({'status':True,'data':serializer.data,'message':'Cities successfully displayed'},status=status.HTTP_200_OK)
        if request.query_params.get('show_all') is not None:
            cities_list = CitiesModel.objects.all()
            serializer = CitiesSerializer(paginated_cities,  many = True)
            return Response({'status':True,'data':serializer.data,'message':'Cities successfully displayed'},status=status.HTTP_200_OK)

        else:
            cities_list = CitiesModel.objects.filter(is_active=True)
            paginated_cities = self.paginate_queryset(cities_list, request, view=self)
            serializer = CitiesSerializer(paginated_cities, many = True)
            paginated_response = self.get_paginated_response(serializer.data).data
            return Response({'status':True,'data':serializer.data,'total_pages': paginated_response.get('total_pages'), 'count': paginated_response.get('count'),'message':'Cities successfully displayed'},status=status.HTTP_200_OK)

    def post(self, request, format=None):
        serializer = CitiesSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({'status': True, 'message': 'City Added!'}, status=status.HTTP_201_CREATED)
        return Response({"status": True, "message": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    

class InquiryAPI(APIView):
    permission_classes = [AllowAny]
    def post(self, request, format=None):
        try:
            serializer = InquirySerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response({'status': True, 'message': 'Inquiry Added!'}, status=status.HTTP_201_CREATED)
            return Response({"status": True, "message": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        
        except Exception as e:
            return Response({"status": True, "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
    
