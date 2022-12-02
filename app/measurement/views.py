
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from rest_framework.response import Response
from django_filters import rest_framework as filters
from squac.filters import CharInFilter, NumberInFilter
from measurement.aggregates.percentile import Percentile
from django.db.models import Avg, StdDev, Min, Max, Count, FloatField
from django.db.models.functions import (Coalesce, Abs, Least, Greatest)
from squac.mixins import (SetUserMixin, DefaultPermissionsMixin,
                          AdminOrOwnerPermissionMixin)
from .exceptions import MissingParameterException
from .models import (Metric, Measurement,
                     Alert, ArchiveDay, ArchiveWeek, ArchiveMonth,
                     ArchiveHour, Monitor, Trigger)
from measurement import serializers
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from measurement.params import measurement_params


def check_measurement_params(params):
    '''ensure that each request for measurements/archives and aggs has:
        * channel or group
        * metric
        * starttime
        * endtime
    '''
    if 'nslc' not in params and 'channel' not in params and 'group' \
            not in params or (not all([p in params for p in
                                       ("metric", "starttime", "endtime")])):
        raise MissingParameterException


'''Filters'''


class MetricFilter(filters.FilterSet):
    # CharInFilter is custom filter see imports
    name = CharInFilter(lookup_expr='in')
    order = filters.OrderingFilter(
        fields=(('name', 'name'),
                ('code', 'code'),
                ('unit', 'unit'),
                ('default_minval', 'default_minval'),
                ('default_maxval', 'default_maxval'),
                ('sample_rate', 'sample_rate')))


class MeasurementFilter(filters.FilterSet):
    """filters measurment by metric, channel, starttime,
        and endtime (starttime)"""
    starttime = filters.CharFilter(field_name='starttime', lookup_expr='gte')
    nslc = CharInFilter(field_name='channel__nslc', lookup_expr='in')

    ''' Note although param is called endtime, it uses starttime, which is
        the the only field with an index
    '''
    endtime = filters.CharFilter(field_name='starttime', lookup_expr='lt')
    metric = NumberInFilter(field_name='metric')
    channel = NumberInFilter(field_name='channel')
    group = NumberInFilter(field_name='channel__group')
    order = filters.OrderingFilter(
        fields=(('starttime', 'starttime'),
                ('endtime', 'endtime'),
                ('metric', 'metric'),
                ('channel__nslc', 'channel')),
    )


class MonitorFilter(filters.FilterSet):
    class Meta:
        model = Monitor
        fields = ('channel_group', 'metric')


class TriggerFilter(filters.FilterSet):
    class Meta:
        model = Trigger
        fields = ('monitor',)


class AlertFilter(filters.FilterSet):
    """filters alert by trigger, in_alarm, timestamp"""
    timestamp_gte = filters.CharFilter(field_name='timestamp',
                                       lookup_expr='gte')
    timestamp_lt = filters.CharFilter(field_name='timestamp',
                                      lookup_expr='lt')

    order = filters.OrderingFilter(
        fields=(('trigger', 'trigger'),
                ('trigger__monitor__name', 'monitor'),
                ('timestamp', 'timestamp'),
                ('in_alarm', 'in_alarm')),
    )

    class Meta:
        model = Alert
        fields = ('trigger', 'in_alarm')


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
    filter_class = MeasurementFilter

    @swagger_auto_schema(manual_parameters=measurement_params)
    def list(self, request, *args, **kwargs):
        check_measurement_params(request.query_params)
        return super().list(self, request, *args, **kwargs)


'''Viewsets'''


class MetricViewSet(MeasurementBaseViewSet):
    serializer_class = serializers.MetricSerializer
    filter_class = MetricFilter

    def get_queryset(self):
        return Metric.objects.all()

    @method_decorator(cache_page(60 * 10, key_prefix="MetricView"))
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)


@method_decorator(name='create', decorator=swagger_auto_schema(
    request_body=serializers.MeasurementSerializer(many=True),
    operation_description="post list of measurements",
    responses={201: openapi.Response(
        "created measurements", serializers.MeasurementSerializer(many=True))}
))
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
        return Measurement.objects.all().order_by('starttime')

    @swagger_auto_schema(manual_parameters=measurement_params)
    def list(self, request, *args, **kwargs):
        '''We want to be careful about large queries so require params'''
        check_measurement_params(request.query_params)
        return super().list(self, request, *args, **kwargs)


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
    serializer_class = serializers.ArchiveHourSerializer

    def get_queryset(self):
        return ArchiveHour.objects.all()


class ArchiveDayViewSet(ArchiveBaseViewSet):
    serializer_class = serializers.ArchiveDaySerializer

    def get_queryset(self):
        return ArchiveDay.objects.all()


class ArchiveWeekViewSet(ArchiveBaseViewSet):
    serializer_class = serializers.ArchiveWeekSerializer

    def get_queryset(self):
        return ArchiveWeek.objects.all()


class ArchiveMonthViewSet(ArchiveBaseViewSet):
    serializer_class = serializers.ArchiveMonthSerializer

    def get_queryset(self):
        return ArchiveMonth.objects.all()


class AggregatedViewSet(IsAuthenticated, viewsets.ViewSet):
    ''' calculate aggregates from raw data
        this is NOT a model viewset so filter_class and serializer_class
        cannot be used
    '''

    @swagger_auto_schema(
        query_serializer=serializers.AggregatedParametersSerializer,
        manual_parameters=measurement_params)
    def list(self, request):
        params = request.query_params
        check_measurement_params(params)
        measurements = Measurement.objects.all()
        # determine if this is a list of channels or list of channel groups
        try:
            channels = [
                int(x) for x in params['channel'].strip(',').split(',')]
            measurements = measurements.filter(channel__in=channels)
        except KeyError:
            '''list of channel groups'''
            try:
                groups = [int(x)
                          for x in params['group'].strip(',').split(',')]
                measurements = measurements.filter(
                    channel__group__in=groups)
            except KeyError:
                '''list of nslcs'''
                channels = [
                    str(x).lower() for x in params['nslc']
                    .strip(',').split(',')
                ]
                measurements = measurements.filter(channel__nslc__in=channels)

        metrics = [int(x) for x in params['metric'].split(',')]
        measurements = measurements.filter(metric__in=metrics)
        measurements = measurements.filter(
            starttime__gte=params['starttime']).filter(
            starttime__lt=params['endtime'])
        aggs = measurements.values(
            'channel', 'metric').annotate(
                mean=Avg('value'),
                median=Percentile('value', percentile=0.5),
                min=Min('value'),
                max=Max('value'),
                minabs=Least(Abs(Min('value')), Abs(Max('value'))),
                maxabs=Greatest(Abs(Min('value')), Abs(Max('value'))),
                stdev=Coalesce(StdDev('value', sample=True), 0,
                               output_field=FloatField()),
                p05=Percentile('value', percentile=0.05),
                p10=Percentile('value', percentile=0.10),
                p90=Percentile('value', percentile=0.90),
                p95=Percentile('value', percentile=0.95),
                num_samps=Count('value'),
                starttime=Min('starttime'),
                endtime=Max('endtime')
        )

        # Get the latest value for each channel-metric
        # The first empty order_by() clears any previous orderings
        latest = measurements.order_by().order_by(
            'channel', 'metric', '-starttime').distinct(
            'channel', 'metric').values(
            'channel', 'metric', 'value')

        # Convert to dict with (channel, metric) key for easy lookup
        latest_dict = {(obj['channel'], obj['metric']): obj['value']
                       for obj in latest}

        # Add in the latest measurement for each channel-metric to aggs. Do
        # this separately since using a subquery was taxing the db too much.
        aggs_list = list(aggs)
        for obj in aggs_list:
            key = (obj['channel'], obj['metric'])
            obj['latest'] = latest_dict.get(key, None)

        serializer = serializers.AggregatedSerializer(
            instance=aggs_list, many=True)
        return Response(serializer.data)
