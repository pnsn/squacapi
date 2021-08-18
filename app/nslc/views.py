from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_headers
from django.core.cache import cache
from django.conf import settings
from rest_framework import viewsets
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.reverse import reverse
from django_filters import rest_framework as filters
from squac.filters import CharInFilter
from squac.mixins import SetUserMixin, DefaultPermissionsMixin
from .models import Network, Channel, Group
from nslc.serializers import NetworkSerializer, ChannelSerializer, \
    GroupSerializer, GroupDetailSerializer


"""Filter classes used for view filtering"""

''''
All query values are case insensitive.
perform 'in' query for network param
    /networks?network=uw,uo,cc
perform exact case for station
    /networks?station=rcm
perform regex SQL 'LIKE' for channel
    /networks?channel=ez
'''


class NetworkFilter(filters.FilterSet):
    network = CharInFilter(field_name='code', lookup_expr='in')
    channel = filters.CharFilter(field_name='channels__code')


class ChannelFilter(filters.FilterSet):
    network = CharInFilter(field_name='network__code')
    net_search = filters.CharFilter(field_name='network__code',
                                    lookup_expr='iregex')
    channel = CharInFilter(field_name='code', lookup_expr='in')
    chan_search = filters.CharFilter(field_name='code', lookup_expr='iregex')
    station = CharInFilter(field_name='station_code', lookup_expr='in')
    sta_search = filters.CharFilter(field_name='station_code',
                                    lookup_expr='iregex')
    location = filters.CharFilter(field_name='loc')
    loc_search = filters.CharFilter(field_name='loc', lookup_expr='iregex')
    startafter = filters.CharFilter(field_name='starttime', lookup_expr='gte')
    startbefore = filters.CharFilter(field_name='starttime', lookup_expr='lte')
    endafter = filters.CharFilter(field_name='endtime', lookup_expr='gte')
    endbefore = filters.CharFilter(field_name='endtime', lookup_expr='lte')
    lat_min = filters.NumberFilter(field_name='lat', lookup_expr='gte')
    lat_max = filters.NumberFilter(field_name='lat', lookup_expr='lte')
    lon_min = filters.NumberFilter(field_name='lon', lookup_expr='gte')
    lon_max = filters.NumberFilter(field_name='lon', lookup_expr='lte')


class GroupFilter(filters.FilterSet):
    class Meta:
        model = Group
        fields = ('name', 'organization')


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


class BaseNslcViewSet(SetUserMixin, DefaultPermissionsMixin,
                      viewsets.ModelViewSet):

    @method_decorator(cache_page(settings.NSLC_DEFAULT_CACHE))
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)


class NetworkViewSet(BaseNslcViewSet):
    serializer_class = NetworkSerializer
    filter_class = NetworkFilter

    def get_queryset(self):
        q = Network.objects.all()
        return self.serializer_class.setup_eager_loading(q)


class ChannelViewSet(BaseNslcViewSet):
    filter_class = ChannelFilter
    serializer_class = ChannelSerializer

    def get_queryset(self):
        q = Channel.objects.all()
        return self.serializer_class.setup_eager_loading(q)


class GroupViewSet(BaseNslcViewSet):
    filter_class = GroupFilter
    serializer_class = GroupSerializer

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return GroupDetailSerializer
        return self.serializer_class

    def get_queryset(self):
        queryset = Group.objects.all()
        return queryset

    @method_decorator(cache_page(60 * 10))
    @method_decorator(vary_on_headers('Cookie'))
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)
