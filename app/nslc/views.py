from rest_framework import viewsets
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.permissions import IsAuthenticated
from django_filters import rest_framework as filters
from squac.permissions import IsAdminOwnerOrPublicReadOnly
from squac.filters import CharInFilter
from squac.mixins import SetUserMixin, PermissionsMixin
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
    channel = CharInFilter(field_name='code', lookup_expr='in')
    chan_search = filters.CharFilter(field_name='code', lookup_expr='iregex')
    station = CharInFilter(field_name='station_code', lookup_expr='in')
    location = filters.CharFilter(field_name='loc')
    startafter = filters.CharFilter(field_name='starttime', lookup_expr='gte')
    startbefore = filters.CharFilter(field_name='starttime', lookup_expr='lte')
    endafter = filters.CharFilter(field_name='endtime', lookup_expr='gte')
    endbefore = filters.CharFilter(field_name='endtime', lookup_expr='lte')
    lat_min = filters.NumberFilter(field_name='lat', lookup_expr='gte')
    lat_max = filters.NumberFilter(field_name='lat', lookup_expr='lte')
    lon_min = filters.NumberFilter(field_name='lon', lookup_expr='gte')
    lon_max = filters.NumberFilter(field_name='lon', lookup_expr='lte')


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


class BaseNslcViewSet(SetUserMixin, PermissionsMixin, viewsets.ModelViewSet):
    pass


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
    serializer_class = GroupSerializer
    # commas act as 'ands'
    permission_classes = (
        IsAuthenticated, IsAdminOwnerOrPublicReadOnly)

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return GroupDetailSerializer
        return self.serializer_class

    def get_queryset(self):
        queryset = Group.objects.all()
        if self.request.user.is_staff:
            return queryset
        '''view public and own resources'''
        orgs = self.request.user.organizations_organization.all()
        org_ids = [o.id for o in orgs]
        queryset = \
            queryset.filter(user=self.request.user) |\
            queryset.filter(share_all=True) |\
            queryset.filter(organization__in=org_ids, share_org=True)
        return queryset
