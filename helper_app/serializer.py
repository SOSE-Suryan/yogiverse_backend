from rest_framework import serializers
from .models import CountryModel,StatesModel,CitiesModel


class CountriesSerializer(serializers.ModelSerializer):

    all_state = serializers.SerializerMethodField(read_only=True)

    def get_all_state(self, obj):
        get_all_country = StatesModel.objects.filter(country=obj).values()
        return get_all_country

    class Meta:
        model = CountryModel
        fields = '__all__'
        
class StateSerializer(serializers.ModelSerializer):
    country_name = serializers.SerializerMethodField(read_only=True)
    all_cities = serializers.SerializerMethodField(read_only=True)

    def get_all_cities(self, obj):
        get_all_cities = CitiesModel.objects.filter(state=obj).values()
        return get_all_cities

    def get_country_name(self, obj):
        return obj.country.country_name

    class Meta:
        model = StatesModel
        fields = '__all__'


class CitiesSerializer(serializers.ModelSerializer):
    state_name = serializers.SerializerMethodField(read_only=True)
    country_name = serializers.SerializerMethodField(read_only=True)
    # all_country = serializers.SerializerMethodField(read_only=True)
    # all_state= serializers.SerializerMethodField(read_only=True)

    def get_state_name(self, obj):
        return obj.state.name

    def get_country_name(self, obj):
        return obj.country.country_name

    # def get_all_state(self, obj):
    #     get_all_country = CountryModel.objects.filter(id=obj.country.id).values()
    #     return get_all_country

    # def get_all_country(self, obj):
    #     get_all_state = StatesModel.objects.filter(id=obj.state.id).values()
    #     return get_all_state

    class Meta:
        model = CitiesModel
        fields = '__all__'
