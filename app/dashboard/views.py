from rest_framework import viewsets
from rest_framework.authentication import TokenAuthentication, \
    SessionAuthentication
from rest_framework.permissions import BasePermission, SAFE_METHODS

from .models import Dashboard, Widget_Type, Widget
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


class Widget_TypeViewSet(BaseDashboardViewSet):
    serializer_class = serializers.Widget_TypeSerializer
    queryset = Widget_Type.objects.all()


class WidgetViewSet(BaseDashboardViewSet):
    serializer_class = serializers.WidgetSerializer
    queryset = Widget.objects.all()


# class ThresholdViewSet(BaseMeasurementViewSet):
#     serializer_class = serializers.ThresholdSerializer
#     queryset = Threshold.objects.all()


# class AlarmViewSet(BaseMeasurementViewSet):
#     serializer_class = serializers.AlarmSerializer
#     queryset = Alarm.objects.all()


# class TriggerViewSet(BaseMeasurementViewSet):
#     serializer_class = serializers.TriggerSerializer
#     queryset = Trigger.objects.all()
