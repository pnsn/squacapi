from rest_framework import viewsets
from rest_framework.authentication import TokenAuthentication, \
    SessionAuthentication
from rest_framework.permissions import BasePermission, SAFE_METHODS

from .models import DataSource, Metric, Group, MetricGroup, Threshold, Alarm,\
    Trigger, Measurement
from measurement import serializers


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


class BaseMeasurementViewSet(viewsets.ModelViewSet):
    '''base class for measurement viewsets:

    Permissions are IsAuthenticatedOrReadOnly
    This allows auth user full crud but unauthorized user to only view
    '''

    authentication_classes = (TokenAuthentication, SessionAuthentication)
    permission_classes = (ObjPermissionOrReadOnly, )

    # all models require an auth user, set on create
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class DataSourceViewSet(BaseMeasurementViewSet):
    serializer_class = serializers.DataSourceSerializer
    # filter_class = DataSourceFilter
    queryset = DataSource.objects.all()


class MetricViewSet(BaseMeasurementViewSet):
    serializer_class = serializers.MetricSerializer
    queryset = Metric.objects.all()


class MeasurementViewSet(BaseMeasurementViewSet):
    serializer_class = serializers.MeasurementSerializer
    queryset = Measurement.objects.all()


class GroupViewSet(BaseMeasurementViewSet):
    serializer_class = serializers.GroupSerializer
    queryset = Group.objects.all()


class MetricGroupViewSet(BaseMeasurementViewSet):
    serializer_class = serializers.MetricGroupSerializer
    queryset = MetricGroup.objects.all()


class ThresholdViewSet(BaseMeasurementViewSet):
    serializer_class = serializers.ThresholdSerializer
    queryset = Threshold.objects.all()


class AlarmViewSet(BaseMeasurementViewSet):
    serializer_class = serializers.AlarmSerializer
    queryset = Alarm.objects.all()


class TriggerViewSet(BaseMeasurementViewSet):
    serializer_class = serializers.TriggerSerializer
    queryset = Trigger.objects.all()
