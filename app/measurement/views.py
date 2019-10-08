from rest_framework import viewsets
from rest_framework.authentication import TokenAuthentication, \
    SessionAuthentication
from rest_framework.permissions import IsAuthenticated

from .models import Metric, Measurement
from measurement import serializers
from .exceptions import MissingParameterException
from squac.filters import in_sql
from django_filters import rest_framework as filters


class MetricFilter(filters.FilterSet):
    name = filters.CharFilter(
        field_name='name', method=in_sql)

    class Meta:
        model = Metric
        # These need to match column names or filter vars from above
        fields = ['name']


class BaseMeasurementViewSet(viewsets.ModelViewSet):
    '''base class for measurement viewsets '''

    authentication_classes = (TokenAuthentication, SessionAuthentication)
    permission_classes = (IsAuthenticated, )
    filter_backends = (filters.DjangoFilterBackend,)

    # all models require an auth user, set on create
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class MetricViewSet(BaseMeasurementViewSet):
    serializer_class = serializers.MetricSerializer
    filter_class = MetricFilter
    queryset = Metric.objects.all()


class MeasurementViewSet(BaseMeasurementViewSet):
    serializer_class = serializers.MeasurementSerializer
    queryset = Measurement.objects.all().order_by('channel', 'metric')

    def get_serializer(self, *args, **kwargs):
        """Allow bulk update

        if an array is passed, set serializer to many
        """
        if isinstance(kwargs.get('data', {}), list):
            kwargs['many'] = True
        return super(MeasurementViewSet, self).get_serializer(*args, **kwargs)

    def _params_to_ints(self, qs):
        # Convert a list of string IDs to a list of integers
        return [int(str_id) for str_id in qs.split(',')]

    def get_queryset(self):
        # Filter measurements by metric, channel, start and end times
        # All 4 params are required for filter to function
        queryset = self.queryset
        pk = self.kwargs.get('pk')
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
