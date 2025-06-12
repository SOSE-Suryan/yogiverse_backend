from rest_framework.pagination import PageNumberPagination
from collections import OrderedDict
from rest_framework.response import Response
import math

class MainPagination(PageNumberPagination):
    page_size = 10  # Set your desired page size
    # page_size_query_param = 'page_size'
    max_page_size = 100  # Set the maximum page size
    orphans = 11
    def get_paginated_response(self, data):
        total_pages = math.ceil(self.page.paginator.count / self.page_size)
        return OrderedDict([
            ('count', self.page.paginator.count),
            ('rows_per_page', self.page_size),
            ('total_pages', total_pages),
            ('current_page', self.page.number),
            ('next', self.get_next_link()),
            ('previous', self.get_previous_link()),
            ('results', data)
        ])