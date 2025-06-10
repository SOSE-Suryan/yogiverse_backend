from django.db import models

# Create your models here.
class CountryModel(models.Model):
    country_name = models.CharField(
        verbose_name='name', max_length=255, unique=True)
    country_code = models.CharField(verbose_name='country code', max_length=3)
    currency = models.CharField(max_length=3)
    calling_code = models.CharField(max_length=10)

    class Meta:
        verbose_name = 'country'
        verbose_name_plural = 'countries'

    def __str__(self):
        return self.country_name


class StatesModel(models.Model):
    country = models.ForeignKey(CountryModel, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name


class CitiesModel(models.Model):
    country = models.ForeignKey(CountryModel, on_delete=models.CASCADE)
    state = models.ForeignKey(StatesModel, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name
