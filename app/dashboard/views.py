from rest_framework import viewsets
from django.views.decorators.cache import cache_control
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_headers
from django.views.decorators.cache import cache_control
# from rest_framework.permissions import IsAuthenticated, IsAdminUser
from squac.mixins import SetUserMixin, DefaultPermissionsMixin, \
    SharedPermissionsMixin
from dashboard.models import Dashboard, Widget
from dashboard import serializers
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from django.core.cache import cache


class BaseDashboardViewSet(SetUserMixin, DefaultPermissionsMixin,
                           viewsets.ModelViewSet):
    pass


class DashboardViewSet(SharedPermissionsMixin, BaseDashboardViewSet):
    serializer_class = serializers.DashboardSerializer

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


class WidgetViewSet(BaseDashboardViewSet):

    serializer_class = serializers.WidgetSerializer

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

    @cache_control(must_revalidate=True, max_age=60)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def get_serializer_class(self):
        if self.action == 'retrieve' or self.action == 'list':
            return serializers.WidgetDetailSerializer
        return self.serializer_class
