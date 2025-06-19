from django.urls import path
from user_app.view.UserCreationView import VendorRegisterView,ProfileView,UserProfileView
from user_app.view.LoginView import  PasswordLoginView,LogoutView  #SendOtp,VerifyOtp
from user_app.view.FCMTokenView import FCMTokenView
from user_app.view.CategoryView import MainSubCategoryAPI
from .views import *
from rest_framework_simplejwt.views import (
    TokenRefreshView,TokenObtainPairView
)
from user_app.view.CategoryViews import MainCategoryListAPIView, SubCategoryListAPIView

urlpatterns = [
    path('vendor_register/',VendorRegisterView.as_view(),name ='create-vendor'),
    path('login/', PasswordLoginView.as_view(), name='password-login'),
    path('logout/', LogoutView.as_view(), name='logout'),

    path('token/',TokenObtainPairView.as_view(),name ='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    path('deactivate/', DeactivateAccountAPI.as_view(), name='deactivate'),
    path('change-password/', ChangePasswordView.as_view(), name='change_password'),
    path('reset-password/', ResetPasswordSendLinkView.as_view(),name='reset_password'),
    path('reset-password/<str:reset_token>/',ResetPasswordFormView.as_view(), name='reset_password'),

    path('fcm-token/', FCMTokenView.as_view(), name='fcm_token'),
    path('profile/', ProfileView.as_view(), name='profile'),
<<<<<<< HEAD
    path('profile/<int:id>/', ProfileView.as_view(), name='update-profile'),
    
    path('user_profile/<int:id>/', UserProfileView.as_view(), name='profile'),
    
    
    path('main_with_sub_categories/', MainSubCategoryAPI.as_view(), name='main_categories'),
    path('main_with_sub_categories/<int:pk>/', MainSubCategoryAPI.as_view(), name='main_categories_with_id'),
    
    # path('sub_categories/', SubCategoryAPI.as_view(), name='sub_categories'),
    # path('sub_categories/<int:pk>/', SubCategoryAPI.as_view(), name='sub_categories_with_id'),
=======
    path('profile/<int:id>/', ProfileView.as_view(), name='profile'),
    path('main-categories/', MainCategoryListAPIView.as_view(), name='main-category-list'),
    path('sub-categories/', SubCategoryListAPIView.as_view(), name='sub-category-list'),

>>>>>>> c1223422bf62402b42093c770b5554a857ea6d89
        
    # login via otp.... view filename : OTPLoginView.py
    # path('send-otp/', SendOtp.as_view(), name='send-otp-to-user'),
    # path('verify-otp/', VerifyOtp.as_view(), name='verify-otp-for-user'),
]
