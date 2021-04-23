from rest_framework import viewsets
from rest_framework.response import Response
from django_filters import rest_framework as filters
from squac.filters import CharInFilter, NumberInFilter
from measurement.aggregates.percentile import Percentile
from django.db.models import (Avg, StdDev, Min, Max, Count, FloatField)
from django.db.models.functions import (Coalesce)
from squac.mixins import (SetUserMixin, DefaultPermissionsMixin,
                          AdminOrOwnerPermissionMixin)
from .exceptions import MissingParameterException
from .models import (Metric, Measurement, Threshold,
                     Alert, ArchiveDay, ArchiveWeek, ArchiveMonth,
                     ArchiveHour, Monitor, Trigger)
from measurement import serializers


def check_measurement_params(params):
    '''ensure that each request for measurements/archives and aggs has:
        * channel or group
        * metric
        * starttime
        * endtime
    '''
    if 'channel' not in params and 'group' not in params or \
            (not all([p in params
                      for p in ("metric", "starttime", "endtime")])):
        raise MissingParameterException


'''Filters'''


class MetricFilter(filters.FilterSet):
    # CharInFilter is custom filter see imports
    name = CharInFilter(lookup_expr='in')


class ThresholdFilter(filters.FilterSet):
    class Meta:
        model = Threshold
        fields = ('metric', 'widget')


class MeasurementFilter(filters.FilterSet):
    """filters measurment by metric, channel, starttime,
        and endtime (starttime)"""
    starttime = filters.CharFilter(field_name='starttime', lookup_expr='gte')

    ''' Note although param is called endtime, it uses starttime, which is
        the the only field with an index
    '''
    endtime = filters.CharFilter(field_name='starttime', lookup_expr='lte')
    metric = NumberInFilter(field_name='metric')
    channel = NumberInFilter(field_name='channel')
    group = NumberInFilter(field_name='channel__group')


class MonitorFilter(filters.FilterSet):
    class Meta:
        model = Monitor
        fields = ('channel_group', 'metric')


class TriggerFilter(filters.FilterSet):
    class Meta:
        model = Trigger
        fields = ('monitor',)


class AlertFilter(filters.FilterSet):
    class Meta:
        model = Alert
        fields = ('trigger', 'in_alarm')


class ArchiveBaseFilter(filters.FilterSet):
    """filters archives by metric, channel, starttime, endtime"""
    starttime = filters.CharFilter(field_name='starttime', lookup_expr='gte')
    endtime = filters.CharFilter(field_name='endtime', lookup_expr='lte')


class ArchiveHourFilter(ArchiveBaseFilter):

    class Meta:
        model = ArchiveHour
        fields = ('metric', 'channel')


class ArchiveDayFilter(ArchiveBaseFilter):

    class Meta:
        model = ArchiveDay
        fields = ('metric', 'channel')


class ArchiveWeekFilter(ArchiveBaseFilter):

    class Meta:
        model = ArchiveWeek
        fields = ('metric', 'channel')


class ArchiveMonthFilter(ArchiveBaseFilter):

    class Meta:
        model = ArchiveMonth
        fields = ('metric', 'channel')


'''Base Viewsets'''


class MeasurementBaseViewSet(SetUserMixin, DefaultPermissionsMixin,
                             viewsets.ModelViewSet):
    pass


class MonitorBaseViewSet(SetUserMixin, AdminOrOwnerPermissionMixin,
                         viewsets.ModelViewSet):
    '''only owner can see monitors and alert'''
    pass


class ArchiveBaseViewSet(DefaultPermissionsMixin,
                         viewsets.ReadOnlyModelViewSet):
    """Viewset that provides access to Archive data

        since there is not a user set on archive, all permissions will be
        model
    """

    REQUIRED_PARAMS = ("metric", "channel", "starttime", "endtime")

    def list(self, request, *args, **kwargs):
        if not all([required_param in request.query_params
           for required_param in self.REQUIRED_PARAMS]):
            raise MissingParameterException

        return super().list(self, request, *args, **kwargs)


'''Viewsets'''


class MetricViewSet(MeasurementBaseViewSet):
    serializer_class = serializers.MetricSerializer
    filter_class = MetricFilter

    def get_queryset(self):
        return Metric.objects.all()


class MeasurementViewSet(MeasurementBaseViewSet):
    '''end point for using channel filter'''
    serializer_class = serializers.MeasurementSerializer
    filter_class = MeasurementFilter

    def get_serializer(self, *args, **kwargs):
        """Allow bulk update

        if an array is passed, set serializer to many
        """
        if isinstance(kwargs.get('data', {}), list):
            kwargs['many'] = True
        return super(MeasurementViewSet, self).get_serializer(*args, **kwargs)

    def get_queryset(self):
        return Measurement.objects.all().order_by('channel', 'metric')

    def list(self, request, *args, **kwargs):
        '''We want to be carful about large querries so require params'''
        check_measurement_params(request.query_params)
        return super().list(self, request, *args, **kwargs)


class ThresholdViewSet(MonitorBaseViewSet):
    serializer_class = serializers.ThresholdSerializer
    filter_class = ThresholdFilter

    def get_queryset(self):
        return Threshold.objects.all()


class MonitorViewSet(MonitorBaseViewSet):
    serializer_class = serializers.MonitorSerializer
    filter_class = MonitorFilter

    def get_queryset(self):
        queryset = Monitor.objects.all()
        if self.request.user.is_staff:
            return queryset
        return queryset.filter(user=self.request.user)

    def get_serializer_class(self):
        if self.action == 'retrieve' or self.action == 'list':
            return serializers.MonitorDetailSerializer
        return self.serializer_class


class TriggerViewSet(MonitorBaseViewSet):
    serializer_class = serializers.TriggerSerializer
    filter_class = TriggerFilter

    def get_queryset(self):
        queryset = Trigger.objects.all()
        if self.request.user.is_staff:
            return queryset
        return queryset.filter(user=self.request.user)


class AlertViewSet(MonitorBaseViewSet):
    serializer_class = serializers.AlertSerializer
    filter_class = AlertFilter

    def get_queryset(self):
        queryset = Alert.objects.all().order_by('-timestamp')
        if self.request.user.is_staff:
            return queryset
        return queryset.filter(user=self.request.user)

    def get_serializer_class(self):
        if self.action == 'retrieve' or self.action == 'list':
            return serializers.AlertDetailSerializer
        return self.serializer_class


class ArchiveHourViewSet(ArchiveBaseViewSet):

    filter_class = ArchiveHourFilter
    serializer_class = serializers.ArchiveHourSerializer

    def get_queryset(self):
        return ArchiveHour.objects.all()


class ArchiveDayViewSet(ArchiveBaseViewSet):

    filter_class = ArchiveDayFilter
    serializer_class = serializers.ArchiveDaySerializer

    def get_queryset(self):
        return ArchiveDay.objects.all()


class ArchiveWeekViewSet(ArchiveBaseViewSet):

    filter_class = ArchiveWeekFilter
    serializer_class = serializers.ArchiveWeekSerializer

    def get_queryset(self):
        return ArchiveWeek.objects.all()


class ArchiveMonthViewSet(ArchiveBaseViewSet):

    filter_class = ArchiveMonthFilter
    serializer_class = serializers.ArchiveMonthSerializer

    def get_queryset(self):
        return ArchiveMonth.objects.all()


class AggregatedViewSet(DefaultPermissionsMixin, viewsets.ViewSet):
    ''' calculate aggregates from raw data
        this is NOT a model viewset so filter_class and serializer_class
        cannot be used
    '''

    def list(self, request):
        params = request.query_params
        check_measurement_params(params)
        measurements = Measurement.objects.all()
        try:
            channels = [int(x) for x in params['channel'].split(',')]
            measurements = measurements.filter(channel__in=channels)
        except KeyError:
            groups = [int(x) for x in params['group'].split(',')]
            measurements = measurements.filter(
                channel__group__in=groups)
        measurements = measurements.filter(
            metric=params['metric']).filter(
            starttime__gte=params['starttime']).filter(
            starttime__lte=params['endtime'])
        aggs = measurements.values(
            'channel', 'metric').annotate(
                mean=Avg('value'),
                median=Percentile('value', percentile=0.5),
                min=Min('value'),
                max=Max('value'),
                stdev=Coalesce(StdDev('value', sample=True), 0,
                               output_field=FloatField()),
                num_samps=Count('value'),
                starttime=Min('starttime'),
                endtime=Max('endtime'),

        )
        serializer = serializers.AggregatedSerializer(
            instance=aggs, many=True)
        return Response(serializer.data)
