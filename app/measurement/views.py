from rest_framework import viewsets
from django_filters import rest_framework as filters
from squac.filters import CharInFilter, NumberInFilter
from squac.mixins import SetUserMixin, DefaultPermissionsMixin
from .exceptions import MissingParameterException
from .models import (Metric, Measurement, Threshold, Monitor, AlarmThreshold,
                     Alert, Archive)
from measurement import serializers


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


class AlarmThresholdFilter(filters.FilterSet):
    class Meta:
        model = AlarmThreshold
        fields = ('alarm',)


class AlertFilter(filters.FilterSet):
    class Meta:
        model = Alert
        fields = ('alarm_threshold', 'in_alarm')


class ArchiveFilter(filters.FilterSet):
    """filters archives by metric, channel, starttime, type, and endtime"""
    starttime = filters.CharFilter(field_name='starttime', lookup_expr='gte')
    endtime = filters.CharFilter(field_name='endtime', lookup_expr='lte')

    class Meta:
        model = Archive
        fields = ('metric', 'channel', 'archive_type')


class BaseMeasurementViewSet(SetUserMixin, DefaultPermissionsMixin,
                             viewsets.ModelViewSet):
    pass


class MetricViewSet(BaseMeasurementViewSet):
    serializer_class = serializers.MetricSerializer
    filter_class = MetricFilter

    def get_queryset(self):
        return Metric.objects.all()


class MeasurementViewSet(BaseMeasurementViewSet):
    '''end point for using channel filter'''
    REQUIRED_PARAMS = ("metric", "starttime", "endtime")
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
        if not all([required_param in request.query_params
                    for required_param in self.REQUIRED_PARAMS]):
            raise MissingParameterException
        return super().list(self, request, *args, **kwargs)


class ThresholdViewSet(BaseMeasurementViewSet):
    serializer_class = serializers.ThresholdSerializer
    filter_class = ThresholdFilter

    def get_queryset(self):
        return Threshold.objects.all()


class MonitorViewSet(SetUserMixin, viewsets.ModelViewSet):
    serializer_class = serializers.MonitorSerializer
    filter_class = MonitorFilter

    def get_queryset(self):
        return Monitor.objects.all()


class AlarmThresholdViewSet(SetUserMixin, viewsets.ModelViewSet):
    serializer_class = serializers.AlarmThresholdSerializer
    filter_class = AlarmThresholdFilter

    def get_queryset(self):
        return AlarmThreshold.objects.all()


class AlertViewSet(SetUserMixin, viewsets.ModelViewSet):
    serializer_class = serializers.AlertSerializer
    filter_class = AlertFilter

    def get_queryset(self):
        return Alert.objects.all()


class ArchiveViewSet(DefaultPermissionsMixin, viewsets.ReadOnlyModelViewSet):
    """Viewset that provides access to Archive data

        since there is not a user set on archive, all permissions will be
        model
    """

    REQUIRED_PARAMS = ("metric", "channel", "starttime", "endtime")
    serializer_class = serializers.ArchiveSerializer
    filter_class = ArchiveFilter

    def get_queryset(self):
        return Archive.objects.all()

    def list(self, request, *args, **kwargs):
        if not all([required_param in request.query_params
           for required_param in self.REQUIRED_PARAMS]):
            raise MissingParameterException

        return super().list(self, request, *args, **kwargs)
