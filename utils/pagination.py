from rest_framework.pagination import PageNumberPagination

class StandardResultsSetPagination(PageNumberPagination):
    """Allow client to control page size with a limit"""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100
