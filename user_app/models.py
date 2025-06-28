from django.db import models
from django.contrib.auth.models import (AbstractBaseUser, BaseUserManager,
                                        Group, PermissionsMixin)
from django.utils import timezone
from phonenumber_field.modelfields import PhoneNumberField
from helper_app.models import CountryModel,StatesModel,CitiesModel
from uuid import uuid4
# Create your models here.


class AccountManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email,username,password, role,**extra_fields):
        if not email:
            raise ValueError("The email must be set")
        if not username:
            raise ValueError("The username must be set")
        values = [email]
        field_value_map = dict(zip(self.model.REQUIRED_FIELDS, values))
        for field_name, value in field_value_map.items():
            if not value:
                raise ValueError("The {} value must be set".format(field_name))

        email = self.normalize_email(email)
        user = self.model(email=email, username=username,role=role,**extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        # ProfileModel.objects.create(user=user)
        # if role == 'vendor':
        #     VendorProfileModel.objects.create(user=user)
        return user
    
    def create_user(self, email,username, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email,username,password, **extra_fields)

    def create_superuser(self, email, username,password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        role = extra_fields.get('role', 'superuser')
        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self._create_user(email,username,password,role, **extra_fields)

class UserModel(AbstractBaseUser, PermissionsMixin):
    ROLE_CHOICES = (
        ('user', 'User'),
        ('vendor', 'Vendor'),
    )

    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    email = models.EmailField(verbose_name="email address", max_length=255, unique=True)
    phone_no = PhoneNumberField(max_length=20,unique=True,blank=True, null=True)
    username = models.CharField(max_length=30, unique=True, null=True, blank=True)
    country = models.ForeignKey(CountryModel, on_delete=models.CASCADE,blank=True, null=True)
    state = models.ForeignKey(StatesModel, on_delete=models.CASCADE,blank=True, null=True)
    city = models.ForeignKey(CitiesModel, on_delete=models.CASCADE,blank=True, null=True)
    is_active = models.BooleanField(default=True)
    is_delete = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)
    last_login = models.DateTimeField(null=True, blank=True)

    objects = AccountManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ['username','first_name', 'last_name']

    def __str__(self):
        return self.email

    class Meta:
        verbose_name = 'user'
        verbose_name_plural = 'users'
        
class ProfileModel(models.Model):
    user = models.OneToOneField(UserModel, on_delete=models.CASCADE, related_name="profile")
    bio = models.TextField(max_length=255,blank=True, null=True)
    phone_no = PhoneNumberField(max_length=20,unique=True,blank=True, null=True)
    otp = models.IntegerField(blank=True, null=True)
    otp_requested_at = models.DateTimeField(blank=True, null=True)
    profile_picture = models.ImageField(upload_to="profile_pics/", blank=True, null=True)
    profile_link = models.URLField(blank=True, null=True, unique=True)
    
    def __str__(self):
        return self.user.username     


class ProfileExternalLinkModel(models.Model):
    profile = models.ForeignKey(ProfileModel, on_delete=models.CASCADE, related_name="external_links")
    url = models.URLField()
    title = models.CharField(max_length=100, blank=True, null=True)
    
    def __str__(self):
        return f"{self.title or 'Link'} - {self.url}"
    
class MainCategoryModel(models.Model):
    name = models.CharField(max_length=50, unique=True)
    main_category_image=models.ImageField(upload_to='main_category_image/', blank=True, null=True)
    
    def __str__(self):
        return self.name


class SubCategoryModel(models.Model):
    name = models.CharField(max_length=50)
    main_category = models.ForeignKey(MainCategoryModel, on_delete=models.CASCADE, related_name="subcategories")
    sub_category_image=models.ImageField(upload_to='sub_category_image/', blank=True, null=True)

    class Meta:
        unique_together = ('name', 'main_category')

    def __str__(self):
        return f"{self.main_category.name} - {self.name}"  

class VendorProfileModel(models.Model):
    user = models.OneToOneField(UserModel, on_delete=models.CASCADE, related_name="vendor_profile")
    business_name = models.CharField(max_length=255, blank=True, null=True)
    main_categories = models.ManyToManyField(MainCategoryModel, related_name="vendors_main_categories")
    subcategories = models.ManyToManyField(SubCategoryModel, related_name="vendors_subcategories")
    pan_number = models.CharField(max_length=20, blank=True, null=True, db_index=True)
    aadhar_number = models.CharField(max_length=20, blank=True, null=True, db_index=True)
    gst_number = models.CharField(max_length=30, blank=True, null=True, db_index=True)
    pan_document = models.FileField(upload_to='vendor_docs/pan/', blank=True, null=True)
    aadhar_document = models.FileField(upload_to='vendor_docs/aadhar/', blank=True, null=True)
    gst_document = models.FileField(upload_to='vendor_docs/gst/', blank=True, null=True)
    company_registration = models.FileField(upload_to='vendor_docs/company_reg/', blank=True, null=True)
    msme_certificate = models.FileField(upload_to='vendor_docs/msme/', blank=True, null=True)
    
    achievement_awards = models.CharField(max_length=255, blank=True, null=True)
    business_type = models.CharField(max_length=100, blank=True, null=True)
    business_presence = models.CharField(max_length=100, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    logo = models.ImageField(upload_to='vendor_docs/logo/', blank=True, null=True)
    perma_link = models.URLField(blank=True, null=True)
    store_owner = models.CharField(max_length=255, blank=True, null=True, db_index=True)
    vendor_banner = models.ImageField(upload_to='vendor_banner/banners/', blank=True, null=True)
    # Status fields
    STATUS_CHOICES = (
        ('published', 'Published'),
        ('locked', 'Locked'),
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='published', db_index=True)

    VENDOR_STATUS_CHOICES = (
        ('verified', 'Verified'),
        ('unverified', 'Unverified'),
        ('rejected', 'Rejected'),
    )
    vendor_status = models.CharField(max_length=20, choices=VENDOR_STATUS_CHOICES, default='unverified', db_index=True)

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['business_name']),
            models.Index(fields=['pan_number']),
            models.Index(fields=['aadhar_number']),
            models.Index(fields=['gst_number']),
            models.Index(fields=['store_owner']),
            models.Index(fields=['status']),
            models.Index(fields=['vendor_status']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return self.business_name or self.user.username


class PasswordResetLinkModel(models.Model):
    user = models.ForeignKey(UserModel, on_delete=models.CASCADE)
    reset_uuid = models.CharField(default=uuid4, editable=False ,max_length = 255)
    url_link = models.URLField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.reset_uuid.hex
    
    
ch = (('android', 'android'), ('ios', 'ios'), ('web', 'web'), ('desktop', 'desktop'), ('other', 'other'))
class FCMTokenModel(models.Model):
    device_type = models.CharField(max_length=10, choices=ch)
    user = models.ForeignKey(UserModel, on_delete=models.CASCADE, related_name="fcm_tokens")
    token = models.TextField()
    device_name = models.CharField(max_length=255, default='Unknown Device')
    created_on = models.DateTimeField(default=timezone.now)
    
    def __str__(self):
        return f"{self.user.username} - {self.device_type} - {self.token}"