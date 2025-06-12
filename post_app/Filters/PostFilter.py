import django_filters
from ..models import *
        
class PostsFilter(django_filters.FilterSet):
    caption = django_filters.CharFilter(field_name='caption', lookup_expr='icontains')

    class Meta:
        model = Post
        fields = ['caption',]
        # fields = {
        #     'name': ['exact', 'icontains'],
        #     'price': ['exact'],
        #     'category_name': ['__in', 'icontains'],
        # }