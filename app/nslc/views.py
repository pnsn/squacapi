
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.views.decorators.cache import cache_control
from django.conf import settings
from rest_framework import viewsets
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.reverse import reverse
from django_filters import rest_framework as filters
from squac.filters import CharInFilter
from squac.mixins import SetUserMixin, DefaultPermissionsMixin, \
    SharedPermissionsMixin, OverrideParamsMixin
from .models import Network, Channel, Group, MatchingRule
from nslc.serializers import NetworkSerializer, ChannelSerializer, \
    GroupSerializer, GroupDetailSerializer, MatchingRuleSerializer
from django.db.models import Count


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
    order = filters.OrderingFilter(
        fields=(('name', 'name'), ('code', 'network'),)
    )


class ChannelFilter(filters.FilterSet):
    nslc = CharInFilter(field_name='nslc', lookup_expr='in')
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
    order = filters.OrderingFilter(
        fields=(('nslc', 'nslc'),
                ('network__code', 'network'),
                ('station_code', 'station'),
                ('loc', 'location'),
                ('code', 'channel'),
                ('starttime', 'starttime'),
                ('endtime', 'endtime')),

    )


class GroupFilter(filters.FilterSet):
    order = filters.OrderingFilter(
        fields=(('name', 'name'), ('organization',
                'organization'), ('user__lastname', 'user_lastname'),
                ('user__firstname', 'user_firstname')),
    )

    class Meta:
        model = Group
        fields = ('name', 'organization', 'user')


class RuleFilter(filters.FilterSet):
    class Meta:
        model = MatchingRule
        fields = ('group',)


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
    destroy
"""


class BaseNslcViewSet(SetUserMixin, DefaultPermissionsMixin,
                      OverrideParamsMixin, viewsets.ModelViewSet):

    pass


class NetworkViewSet(BaseNslcViewSet):
    serializer_class = NetworkSerializer
    filter_class = NetworkFilter

    def get_queryset(self):
        q = Network.objects.all()
        return self.serializer_class.setup_eager_loading(q)

    @method_decorator(cache_page(settings.NSLC_DEFAULT_CACHE,
                                 key_prefix="NetworkView"))
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)


class ChannelViewSet(BaseNslcViewSet):
    filter_class = ChannelFilter
    serializer_class = ChannelSerializer

    def get_queryset(self):
        q = Channel.objects.all()
        return self.serializer_class.setup_eager_loading(q)

    @cache_control(must_revalidate=True, max_age=settings.NSLC_DEFAULT_CACHE)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)


class GroupViewSet(SharedPermissionsMixin, BaseNslcViewSet):
    filter_class = GroupFilter
    serializer_class = GroupSerializer

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return GroupDetailSerializer
        return self.serializer_class

    def get_queryset(self):

        queryset = Group.objects \
            .select_related('user') \
            .annotate(channels_count=Count('channels'))

        if self.request.user.is_staff:
            return queryset
        org = self.request.user.organization
        # get users dash, shared_all dashes and users org shared dashes
        queryset = \
            queryset.filter(user=self.request.user) |\
            queryset.filter(share_all=True) |\
            queryset.filter(organization=org.id, share_org=True)

        return queryset

    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)


class MatchingRuleViewSet(BaseNslcViewSet):
    queryset = MatchingRule.objects.all()
    serializer_class = MatchingRuleSerializer
    filter_class = RuleFilter
