from django.contrib import admin
from .models import CountryModel,StatesModel,CitiesModel
from import_export.admin import ImportExportModelAdmin

# Register your models here.
@admin.register(CountryModel)
class CountryModelAdmin(ImportExportModelAdmin):
    list_display = ('id', 'country_name', 'country_code', 'currency', 'calling_code')
    search_fields = ('country_name', 'country_code', 'currency', 'calling_code')

@admin.register(StatesModel)
class StatesModelAdmin(ImportExportModelAdmin):
    list_display = ('id', 'name', 'country')
    search_fields = ('name', 'country__country_name')
    raw_id_fields = ('country',)

@admin.register(CitiesModel)
class CitiesModelAdmin(ImportExportModelAdmin):
    list_display = ('id', 'name', 'state', 'country', 'is_active')
    search_fields = ('name', 'state__name', 'country__country_name')
    raw_id_fields = ('state', 'country')