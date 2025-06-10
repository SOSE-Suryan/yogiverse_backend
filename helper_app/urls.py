from django.urls import path
from user_app.view.UserCreationView import VendorRegisterView
from .views import *

urlpatterns = [
  
  
    path('countries/', CountriesAPI.as_view(), name='countries'),
    path('countries/<int:pk>/', CountriesAPI.as_view(), name='countries'),
    
    path('states/', StatesAPI.as_view(), name='states'),
    path('states/<int:pk>/', StatesAPI.as_view(), name='states'),
    path('cities/', CitiesAPI.as_view(), name='cities'),
    path('cities/<int:state_id>/', CitiesAPI.as_view(), name='cities')
    
]