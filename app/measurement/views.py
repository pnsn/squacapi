from rest_framework import viewsets
from django_filters import rest_framework as filters
from squac.filters import CharInFilter, NumberInFilter
from squac.mixins import SetUserMixin, DefaultPermissionsMixin
from .exceptions import MissingParameterException
from .models import (Metric, Measurement, Threshold, Alarm, AlarmThreshold,
                     Alert, ArchiveDay, ArchiveWeek, ArchiveMonth,
                     ArchiveHour)
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


class AlarmFilter(filters.FilterSet):
    class Meta:
        model = Alarm
        fields = ('channel_group', 'metric')


class AlarmThresholdFilter(filters.FilterSet):
    class Meta:
        model = AlarmThreshold
        fields = ('alarm',)


class AlertFilter(filters.FilterSet):
    class Meta:
        model = Alert
        fields = ('alarm_threshold', 'in_alarm')


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


class AlarmViewSet(SetUserMixin, viewsets.ModelViewSet):
    serializer_class = serializers.AlarmSerializer
    filter_class = AlarmFilter

    def get_queryset(self):
        return Alarm.objects.all()


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
