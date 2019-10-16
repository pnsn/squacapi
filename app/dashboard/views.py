from rest_framework import viewsets
from rest_framework.authentication import TokenAuthentication, \
    SessionAuthentication
from rest_framework.permissions import IsAuthenticated

from .models import Dashboard, WidgetType, Widget, StatType
from dashboard import serializers


class BaseDashboardViewSet(viewsets.ModelViewSet):
    '''base class for dashboard viewsets'''

    authentication_classes = (TokenAuthentication, SessionAuthentication)
    permission_classes = (IsAuthenticated, )

    # all models require an auth user, set on create
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class DashboardViewSet(BaseDashboardViewSet):
    serializer_class = serializers.DashboardSerializer
    queryset = Dashboard.objects.all()

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return serializers.DashboardDetailSerializer
        return self.serializer_class


class WidgetTypeViewSet(BaseDashboardViewSet):
    serializer_class = serializers.WidgetTypeSerializer
    queryset = WidgetType.objects.all()


class StatTypeViewSet(BaseDashboardViewSet):
    serializer_class = serializers.StatTypeSerializer
    queryset = StatType.objects.all()


class WidgetViewSet(BaseDashboardViewSet):
    serializer_class = serializers.WidgetSerializer
    queryset = Widget.objects.all()

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
            self.serializer_class = serializers.WidgetDetailSerializer

        return queryset

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return serializers.WidgetDetailSerializer
        return self.serializer_class
