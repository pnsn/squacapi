from rest_framework import viewsets
# from rest_framework.permissions import IsAuthenticated, IsAdminUser
from squac.mixins import SetUserMixin, DefaultPermissionsMixin, \
    SharedPermissionsMixin, OverrideParamsMixin, \
    EnablePartialUpdateMixin
from dashboard.models import Dashboard, Widget
from dashboard import serializers
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


class DashboardFilter(filters.FilterSet):
    order = filters.OrderingFilter(
        fields=(('name', 'name'),
                ('organization', 'organization'),
                ('user__lastname', 'user_lastname'),
                ('user__firstname', 'user_firstname'),
                ('description', 'description'),
                ('channel_group__name', 'channel_group')),
    )

    class Meta:
        model = Dashboard
        fields = ('user', 'organization', 'share_all', 'share_org',)


class WidgetFilter(filters.FilterSet):
    class Meta:
        model = Widget
        fields = ('dashboard',)


class BaseDashboardViewSet(SetUserMixin, DefaultPermissionsMixin,
                           OverrideParamsMixin, viewsets.ModelViewSet):
    pass


class DashboardViewSet(SharedPermissionsMixin, BaseDashboardViewSet,
                       EnablePartialUpdateMixin):
    serializer_class = serializers.DashboardSerializer
    filter_class = DashboardFilter

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return serializers.DashboardDetailSerializer
        return self.serializer_class

    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        queryset = Dashboard.objects.all()
        if self.request.user.is_staff:
            return queryset
        org = self.request.user.organization
        # get users dash, shared_all dashes and users org shared dashes
        queryset = \
            queryset.filter(user=self.request.user) |\
            queryset.filter(share_all=True) |\
            queryset.filter(organization=org.id, share_org=True)

        return queryset


class WidgetViewSet(BaseDashboardViewSet, EnablePartialUpdateMixin):
    queryset = Widget.objects.all()
    serializer_class = serializers.WidgetSerializer
    filter_class = WidgetFilter

    def _params_to_ints(self, qs):
        # Convert a list of string IDs to a list of integers
        return [int(str_id) for str_id in qs.split(',')]

    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def get_serializer_class(self):
        if self.action == 'retrieve' or self.action == 'list':
            return serializers.WidgetDetailSerializer
        return self.serializer_class
