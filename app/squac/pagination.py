from rest_framework.pagination import LimitOffsetPagination
'''Custom pagination '''


class OptionalPagination(LimitOffsetPagination):
    '''Pagination class to allow optional pagination
        ådefault to no pagination unless offset set
    '''

    def paginate_queryset(self, queryset, request, view=None):
        if 'offset' not in request.query_params:
            return None
        return super().paginate_queryset(queryset, request)
