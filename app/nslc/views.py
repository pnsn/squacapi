from core.models import Network, Station, Location, Channel
from rest_framework import generics
from nslc.serializers import NetworkSerializer, StationSerializer, \
    LocationSerializer, ChannelSerializer
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.reverse import reverse
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


"""
List and Detail views for all NSLC
"""


class NetworkList(generics.ListAPIView):
    '''Network list view'''
    serializer_class = NetworkSerializer

    # filter_class = NetworkFilter
    def get_queryset(self):
        queryset = Network.objects.all()
        queryset = self.get_serializer_class().setup_eager_loading(queryset)
        return queryset


class NetworkDetail(generics.RetrieveUpdateDestroyAPIView):
    '''Network detail view'''
    serializer_class = NetworkSerializer

    def get_object(self):
        return Network.objects.get(pk=self.kwargs['pk'])


class StationList(generics.ListAPIView):
    serializer_class = StationSerializer
    # filter_class = StationFilter

    def get_queryset(self):
        queryset = Station.objects.all()
        queryset = self.get_serializer_class().setup_eager_loading(queryset)
        return queryset


class StationDetail(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = StationSerializer

    def get_object(self):
        return Station.objects.get(
            pk=self.kwargs['pk'])


class LocationList(generics.ListAPIView):
    serializer_class = LocationSerializer
    # filter_class = LocationFilter

    def get_queryset(self):
        queryset = Location.objects.all()
        queryset = self.get_serializer_class().setup_eager_loading(queryset)
        return queryset


class LocationDetail(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = LocationSerializer
    # filter_class = LocationFilter

    def get_object(self):
        return Location.objects.get(pk=self.kwargs['pk'])


class ChannelList(generics.ListAPIView):
    '''Return list of channels'''
    serializer_class = ChannelSerializer
    # filter_class = ChannelFilter

    def get_queryset(self):
        queryset = Channel.objects.all()
        queryset = self.get_serializer_class().setup_eager_loading(queryset)
        return queryset


class ChannelDetail(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ChannelSerializer

    def get_object(self):
        return Channel.objects.get(pk=self.kwargs['pk'])
