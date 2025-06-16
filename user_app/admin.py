from django.contrib import admin
from .models import UserModel,ProfileModel,MainCategoryModel,SubCategoryModel,VendorProfileModel,FCMTokenModel
from import_export.admin import ImportExportModelAdmin
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin



# Register your models here.
@admin.register(UserModel)
class UserModelAdmin(ImportExportModelAdmin, BaseUserAdmin):
    model = UserModel

    # Fields shown in the list view
    list_display = ('id', 'username', 'email', 'first_name', 'last_name', 'role', 'is_active', 'date_joined')

    # Search functionality
    search_fields = ('username', 'email', 'first_name', 'last_name')

    # Filters on the right side of admin
    list_filter = ('role', 'is_active', 'is_staff', 'date_joined')

    # Default ordering
    ordering = ('-date_joined',)

    # Set fields as read-only
    readonly_fields = ('date_joined', 'last_login')

    # Group fields for user edit/add view
    fieldsets = (
        (None, {'fields': ('username', 'email', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name')}),
        (_('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
        (_('Extra info'), {'fields': ('role',)}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2', 'role', 'is_active', 'is_staff', 'is_superuser')}
        ),
    )

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


@admin.register(FCMTokenModel)
class FCMTokenModelAdmin(ImportExportModelAdmin):
    list_display = ('id', 'user', 'device_type', 'token', 'created_on')[::-1]
    search_fields = ('user__username', 'user__email', 'token')
    raw_id_fields = ('user',)
    readonly_fields = ('created_on',)

