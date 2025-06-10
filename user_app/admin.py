from django.contrib import admin
from .models import UserModel,ProfileModel,MainCategoryModel,SubCategoryModel,VendorProfileModel
from import_export.admin import ImportExportModelAdmin



# Register your models here.
@admin.register(UserModel)
class UserModelAdmin(ImportExportModelAdmin):
    list_display = ('id', 'username', 'email', 'first_name', 'last_name', 'role', 'is_active', 'date_joined')[::-1]
    search_fields = ('username', 'email', 'first_name', 'last_name')
    # list_filter = ('role', 'is_active', 'is_staff', 'date_joined')
    ordering = ('-date_joined',)
    # readonly_fields = ('date_joined', 'last_login')

@admin.register(ProfileModel)
class ProfileModelAdmin(ImportExportModelAdmin):
    list_display = ('id', 'user', 'profile_link', 'bio')[::-1]
    search_fields = ('user__username', 'user__email', 'profile_link')
    raw_id_fields = ('user',)

@admin.register(MainCategoryModel)
class VendorMainCategoryAdmin(ImportExportModelAdmin):
    list_display = ('id', 'name')[::-1]
    search_fields = ('name',)

@admin.register(SubCategoryModel)
class VendorSubCategoryAdmin(ImportExportModelAdmin):
    list_display = ('id', 'name','main_category')[::-1]
    search_fields = ('name',)

@admin.register(VendorProfileModel)
class VendorProfileModelAdmin(ImportExportModelAdmin):
    list_display = (
        'id', 'user', 'business_name', 'vendor_status', 'status', 'store_owner', 'created_at'
    )[::-1]
    search_fields = (
        'user__username', 'user__email', 'business_name', 'pan_number', 'aadhar_number', 'gst_number', 'store_owner'
    )
    # list_filter = ('vendor_status', 'status', 'categories', 'created_at')
    raw_id_fields = ('user',)
    # filter_horizontal = ('categories',)
    readonly_fields = ('created_at', 'updated_at')
