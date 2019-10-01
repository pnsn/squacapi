from rest_framework import viewsets
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.authentication import TokenAuthentication, \
    SessionAuthentication

from rest_framework.permissions import IsAuthenticated

from .models import Network, Channel, Group
from nslc.serializers import NetworkSerializer, ChannelSerializer, \
    GroupSerializer, GroupDetailSerializer
from squac.filters import in_sql, regex_sql

# import django_filters as filters
from django_filters import rest_framework as filters

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
    network = filters.CharFilter(
        field_name='code', method=in_sql)
    channel = filters.CharFilter(
        field_name='channels__code', lookup_expr='iexact')

    class Meta:
        model = Network
        # These need to match column names or filter vars from above
        fields = ['network', 'channel']


class ChannelFilter(filters.FilterSet):
    network = filters.CharFilter(
        field_name='network__code', method=in_sql)
    channel = filters.CharFilter(
        field_name='code', method=regex_sql)

    class Meta:
        model = Channel
        # These need to match column names or filter vars from above
        fields = ['network', 'channel']


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


# class ObjPermissionOrReadOnly(BasePermission):
#     """Object-level permission on scarey methods,
# read only on safe methods """

#     def has_permission(self, request, view):
#         '''http permission?'''

#         # if request.method in SAFE_METHODS:
#         #     return True
#         # user must be authenticated
#         return request.user and request.user.is_authenticated

#     def has_obj_permission(self, request, view, obj):
#         '''object level permissions, set by adding user to group

#         Read permissions are allowed to any request,
#         so we'll always allow GET, HEAD or OPTIONS requests.
#         '''
#         # if request.method in SAFE_METHODS:
#         #     return True

#         # user must have permission
#         return self.check_object_permissions(request, obj)


class BaseNslcViewSet(viewsets.ModelViewSet):
    '''base class for all nslc viewsets:

     Permissions are IsAuthticatedOrReadOnly
        This allows auth user to fully crud but unathorized user to view
        all data
     '''
    authentication_classes = (TokenAuthentication, SessionAuthentication)
    permission_classes = (IsAuthenticated, )
    filter_backends = (filters.DjangoFilterBackend,)

    # all models have require an auth user, set on create
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class NetworkViewSet(BaseNslcViewSet):
    serializer_class = NetworkSerializer
    q = Network.objects.all()
    filter_class = NetworkFilter
    queryset = serializer_class.setup_eager_loading(q)


# class StationViewSet(BaseNslcViewSet):
#     serializer_class = StationSerializer
#     filter_class = StationFilter
#     q = Station.objects.all()
#     queryset = serializer_class.setup_eager_loading(q)


# class LocationViewSet(BaseNslcViewSet):
#     serializer_class = LocationSerializer
#     # filter_class = LocationFilter
#     q = Location.objects.all()
#     queryset = serializer_class.setup_eager_loading(q)


class ChannelViewSet(BaseNslcViewSet):
    serializer_class = ChannelSerializer
    filter_class = ChannelFilter
    q = Channel.objects.all()
    queryset = serializer_class.setup_eager_loading(q)


class GroupViewSet(BaseNslcViewSet):
    serializer_class = GroupSerializer
    queryset = Group.objects.all()

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return GroupDetailSerializer
        return self.serializer_class
