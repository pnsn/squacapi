from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from squac.mixins import SetUserMixin, PermissionsMixin
from squac.permissions import IsAdminOwnerOrPublicReadOnly
from .models import Dashboard, WidgetType, Widget, StatType
from dashboard import serializers


class BaseDashboardViewSet(SetUserMixin, PermissionsMixin,
                           viewsets.ModelViewSet):
    pass


class DashboardViewSet(BaseDashboardViewSet):
    serializer_class = serializers.DashboardSerializer
    permission_classes = (
        IsAuthenticated, IsAdminOwnerOrPublicReadOnly)
    queryset = Dashboard.objects.all()

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return serializers.DashboardDetailSerializer
        return self.serializer_class

    def get_queryset(self):
        queryset = Dashboard.objects.filter(user=self.request.user) | \
            Dashboard.objects.filter(is_public=True)
        return queryset


class WidgetTypeViewSet(BaseDashboardViewSet):
    serializer_class = serializers.WidgetTypeSerializer
    queryset = WidgetType.objects.all()


class StatTypeViewSet(BaseDashboardViewSet):
    serializer_class = serializers.StatTypeSerializer
    queryset = StatType.objects.all()


class WidgetViewSet(BaseDashboardViewSet):

    serializer_class = serializers.WidgetSerializer
    queryset = Widget.objects.all()
    permission_classes = (
        IsAuthenticated, IsAdminOwnerOrPublicReadOnly)

    def _params_to_ints(self, qs):
        # Convert a list of string IDs to a list of integers
        return [int(str_id) for str_id in qs.split(',')]

    def get_queryset(self):
        # Retrieve widget by dashboard id
        dashboard = self.request.query_params.get('dashboard')
        queryset = self.queryset
        if dashboard:
            dashboard_id = self._params_to_ints(dashboard)
            queryset = queryset.filter(dashboard__id__in=dashboard_id)
        queryset = queryset.filter(user=self.request.user) | \
            queryset.filter(is_public=True)
        return queryset

    def get_serializer_class(self):
        if self.action == 'retrieve' or self.action == 'list':
            return serializers.WidgetDetailSerializer
        return self.serializer_class
