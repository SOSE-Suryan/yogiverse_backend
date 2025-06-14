from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

class PaginationWithPageCount(PageNumberPagination):
    def get_paginated_response(self, data):
        return Response({
            'count': self.page.paginator.count,
            'total_pages': self.page.paginator.num_pages,
            'results': data
        })
    
    
class DefaultPaginationClass(PaginationWithPageCount):
    page_size = 10
    max_page_size = 25
    page_query_param = 'page'
    
class ChatDefaultPaginationClass(PaginationWithPageCount):
    page_size = 30
    max_page_size = 25
    page_query_param = 'page'