from django_filters import rest_framework as filters
'''custom filters go here'''


class CharInFilter(filters.BaseInFilter, filters.CharFilter):
    '''mixin required to get SQL 'in' expression to behave as expected'''
    pass
