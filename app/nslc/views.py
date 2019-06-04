from rest_framework import viewsets
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.authentication import TokenAuthentication, \
    SessionAuthentication

from rest_framework.permissions import IsAuthenticated, AllowAny

from .models import Network, Station, Location, Channel
from nslc.serializers import NetworkSerializer, StationSerializer, \
    LocationSerializer, ChannelSerializer
import django_filters as filters

"""Common methods for filtering classes to share"""


def in_sql(queryset, name, value):
    """perform generic 'in' SQL statement exp

    select * from networks where code in ('uw', 'uo')
    """

    if name is not None:
        values = value.lower().split(",")
        name_in = '__'.join([name, 'in'])
        queryset = queryset.filter(**{name_in: values})
    return queryset


def regex_sql(queryset, name, value):
    """perform python regex searches on field"""
    if name is not None:
        name_regex = '__'.join([name, 'iregex'])
        queryset = queryset.filter(**{name_regex: value})
    return queryset


"""Filter classes used for view filtering"""


class NetworkFilter(filters.FilterSet):
    network = filters.CharFilter(
        field_name='code', method=in_sql)
    station = filters.CharFilter(
        field_name='stations__code', lookup_expr='iexact')
    location = filters.CharFilter(
        field_name='station__locations__code', lookup_expr='iexact')
    channel = filters.CharFilter(
        field_name='stations__locations__channels__code', method=regex_sql)


class StationFilter(filters.FilterSet):
    network = filters.CharFilter(
        field_name='network__code', method=in_sql)
    station = filters.CharFilter(
        field_name='code', lookup_expr='iexact')
    location = filters.CharFilter(
        field_name='locations__code', lookup_expr='iexact')
    channel = filters.CharFilter(
        field_name='locations__channels__code', method=regex_sql)


class LocationFilter(filters.FilterSet):
    network = filters.CharFilter(
        field_name='station__network__code', method=in_sql)
    station = filters.CharFilter(
        field_name='station__code', lookup_expr='iexact')
    location = filters.CharFilter(
        field_name='code', lookup_expr='iexact')
    channel = filters.CharFilter(
        field_name='channel_code', method=regex_sql)


class ChannelFilter(filters.FilterSet):
    network = filters.CharFilter(
        field_name='location__station__network__code', method=in_sql)
    station = filters.CharFilter(
        field_name='location__station__code', lookup_expr='iexact')
    location = filters.CharFilter(
        field_name='location__code', lookup_expr='iexact')
    channel = filters.CharFilter(
        field_name='code', method=regex_sql)


@api_view(['GET'])
def api_root(request, format=None):
    '''api root'''
    return Response({
        'nets': reverse('network-list', request=request, format=format),
    })


"""model viewset include all CRUD methods:
    retrieve
    list
    update
    partial_update
    destory
    """


class BaseNslcViewSet(viewsets.ModelViewSet):
    '''base class for all nslc viewsets'''
    authentication_classes = (SessionAuthentication, TokenAuthentication)

    def perform_create(self, serializer):
        '''create an object'''
        serializer.save(user=self.request.user)

    def get_permissions(self):
        '''require auth for non safe methods'''
        if self.action in ['update', 'partial_update', 'destroy']:

            permission_classes = [IsAuthenticated]
        else:
            '''allow any on retrieve'''
            permission_classes = [AllowAny]
        return [permission() for permission in permission_classes]


class NetworkViewSet(BaseNslcViewSet):
    serializer_class = NetworkSerializer
    filter_class = NetworkFilter
    q = Network.objects.all()
    queryset = serializer_class.setup_eager_loading(q)


class StationViewSet(BaseNslcViewSet):
    serializer_class = StationSerializer
    filter_class = StationFilter
    q = Station.objects.all()
    queryset = serializer_class.setup_eager_loading(q)


class LocationViewSet(BaseNslcViewSet):
    serializer_class = LocationSerializer
    filter_class = LocationFilter
    q = Location.objects.all()
    queryset = serializer_class.setup_eager_loading(q)


class ChannelViewSet(BaseNslcViewSet):
    serializer_class = ChannelSerializer
    filter_class = ChannelFilter
    q = Channel.objects.all()
    queryset = serializer_class.setup_eager_loading(q)
