from rest_framework.pagination import PageNumberPagination


class CustomPagination(PageNumberPagination):
    """Limit pagination class."""

    page_size_query_param = 'limit'
