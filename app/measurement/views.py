from rest_framework import viewsets
from rest_framework.authentication import TokenAuthentication, \
    SessionAuthentication
from rest_framework.permissions import BasePermission, SAFE_METHODS

from .models import Metric, Measurement
from measurement import serializers
from .exceptions import MissingParameterException


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


class MetricViewSet(BaseMeasurementViewSet):
    serializer_class = serializers.MetricSerializer
    queryset = Metric.objects.all()


class MeasurementViewSet(BaseMeasurementViewSet):
    serializer_class = serializers.MeasurementSerializer
    queryset = Measurement.objects.all()

    def _params_to_ints(self, qs):
        # Convert a list of string IDs to a list of integers
        return [int(str_id) for str_id in qs.split(',')]

    def get_queryset(self):
        # Filter measurements by metric, channel, start and end times
        # All 4 params are required for filter to function
<<<<<<< HEAD
        queryset = self.queryset
        pk = self.kwargs.get('pk')
=======
>>>>>>> 8939df776c3a3935a4e1b91b0008a9782bbcac12
        metric = self.request.query_params.get('metric')
        chan = self.request.query_params.get('channel')
        stime = self.request.query_params.get('starttime')
        etime = self.request.query_params.get('endtime')
        if pk:
            return queryset.filter(id=pk)
        else:
            if metric and chan and stime and etime:
                metric_ids = self._params_to_ints(metric)
                chan_ids = self._params_to_ints(chan)
                queryset = queryset.filter(metric__id__in=metric_ids)
                queryset = queryset.filter(channel__id__in=chan_ids)
                queryset = queryset.filter(starttime__gte=stime)
                queryset = queryset.filter(endtime__lte=etime)
            else:
                raise MissingParameterException
        return queryset
