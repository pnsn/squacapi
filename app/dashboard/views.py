from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from squac.mixins import SetUserMixin, PermissionsMixin
from squac.permissions import IsAdminOwnerOrShared
from .models import Dashboard, WidgetType, Widget, StatType
from dashboard import serializers


class BaseDashboardViewSet(SetUserMixin, PermissionsMixin,
                           viewsets.ModelViewSet):
    pass


class DashboardViewSet(BaseDashboardViewSet):
    serializer_class = serializers.DashboardSerializer
    permission_classes = (
        IsAuthenticated, IsAdminOwnerOrShared)

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return serializers.DashboardDetailSerializer
        return self.serializer_class

    def get_queryset(self):
        queryset = Dashboard.objects.all()
        if self.request.user.is_staff:
            return queryset
        orgs = self.request.user.organizations_organization.all()
        org_ids = [o.id for o in orgs]
        # get users dash, shared_all dashes and users org shared dashes
        queryset = \
            queryset.filter(user=self.request.user) |\
            queryset.filter(share_all=True) |\
            queryset.filter(organization__in=org_ids, share_org=True)

        return queryset


class WidgetTypeViewSet(BaseDashboardViewSet):
    serializer_class = serializers.WidgetTypeSerializer

    def get_queryset(self):
        return WidgetType.objects.all()


class StatTypeViewSet(PermissionsMixin, viewsets.ReadOnlyModelViewSet):
    ''' we only want readonly through api'''
    serializer_class = serializers.StatTypeSerializer

    def get_queryset(self):
        return StatType.objects.all()


class WidgetViewSet(BaseDashboardViewSet):

    serializer_class = serializers.WidgetSerializer
    permission_classes = (
        IsAuthenticated, IsAdminOwnerOrShared)

    def _params_to_ints(self, qs):
        # Convert a list of string IDs to a list of integers
        return [int(str_id) for str_id in qs.split(',')]

    def get_queryset(self):
        dashboard = self.request.query_params.get('dashboard')
        queryset = Widget.objects.all()
        if dashboard:
            dashboard_id = self._params_to_ints(dashboard)
            queryset = queryset.filter(dashboard__id__in=dashboard_id)
        return queryset

    def get_serializer_class(self):
        if self.action == 'retrieve' or self.action == 'list':
            return serializers.WidgetDetailSerializer
        return self.serializer_class
