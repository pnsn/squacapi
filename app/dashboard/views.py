from rest_framework import viewsets
from rest_framework.authentication import TokenAuthentication, \
    SessionAuthentication
from rest_framework.permissions import BasePermission, SAFE_METHODS

from .models import Dashboard, WidgetType, Widget
from dashboard import serializers


class ObjPermissionOrReadOnly(BasePermission):
    '''Object-level permission on scarey methods, read only on safe methods'''

    def has_permission(self, request, view):
        '''http permission?'''

        if request.method in SAFE_METHODS:
            return True
        # user must be authenticated
        return request.user and request.user.is_authenticated

    def has_obj_permission(self, request, view, obj):
        '''object level permissions, set by adding user to group

        Read permissions are allowed to any request,
        so we'll always allow GET, HEAD or OPTIONS requests.
        '''
        if request.method in SAFE_METHODS:
            return True

        # user must have permission
        return self.check_object_permissions(request, obj)


class BaseDashboardViewSet(viewsets.ModelViewSet):
    '''base class for dashboard viewsets:

    Permissions are IsAuthenticatedOrReadOnly
    This allows auth user full crud but unauthorized user to only view
    '''

    authentication_classes = (TokenAuthentication, SessionAuthentication)
    permission_classes = (ObjPermissionOrReadOnly, )

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

        return queryset
