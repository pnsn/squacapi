from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from django_filters import rest_framework as filters
from squac.filters import CharInFilter, NumberInFilter
from squac.mixins import SetUserMixin, PermissionsMixin
from .exceptions import MissingParameterException
from squac.permissions import IsAdminOwnerOrPublicReadOnly
from .models import Metric, Measurement, Threshold, Archive
from measurement import serializers


class MetricFilter(filters.FilterSet):
    # CharInFilter is custom filter see imports
    name = CharInFilter(lookup_expr='in')


class ThresholdFilter(filters.FilterSet):
    class Meta:
        model = Threshold
        fields = ('metric', 'widget')


class MeasurementFilter(filters.FilterSet):
    """filters measurment by metric, channel, starttime, and endtime"""
    starttime = filters.CharFilter(field_name='starttime', lookup_expr='gte')
    endtime = filters.CharFilter(field_name='endtime', lookup_expr='lte')
    metric = NumberInFilter(field_name='metric')
    channel = NumberInFilter(field_name='channel')


class ArchiveFilter(filters.FilterSet):
    """filters archives by metric, channel, starttime, type, and endtime"""
    starttime = filters.CharFilter(field_name='starttime', lookup_expr='gte')
    endtime = filters.CharFilter(field_name='endtime', lookup_expr='lte')

    class Meta:
        model = Archive
        fields = ('metric', 'channel', 'archive_type')


class BaseMeasurementViewSet(SetUserMixin, PermissionsMixin,
                             viewsets.ModelViewSet):
    pass


class MetricViewSet(BaseMeasurementViewSet):
    serializer_class = serializers.MetricSerializer
    filter_class = MetricFilter
    permission_classes = (
        IsAuthenticated, IsAdminOwnerOrPublicReadOnly)
    queryset = Metric.objects.all()


class MeasurementViewSet(BaseMeasurementViewSet):
    REQUIRED_PARAMS = ("metric", "channel", "starttime", "endtime")
    serializer_class = serializers.MeasurementSerializer
    permission_classes = (
        IsAuthenticated, IsAdminOwnerOrPublicReadOnly)
    q = Measurement.objects.all().order_by('channel', 'metric')
    filter_class = MeasurementFilter
    queryset = serializer_class.setup_eager_loading(q)

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

    def list(self, request, *args, **kwargs):
        if not all([required_param in request.query_params
                    for required_param in self.REQUIRED_PARAMS]):
            raise MissingParameterException

        return super().list(self, request, *args, **kwargs)


class ThresholdViewSet(BaseMeasurementViewSet):
    serializer_class = serializers.ThresholdSerializer
    filter_class = ThresholdFilter
    queryset = Threshold.objects.all()


class ArchiveViewSet(PermissionsMixin, viewsets.ReadOnlyModelViewSet):
    """Viewset that provides access to Archive data

        since there is not a user set on archive, all permissions will be
        model
    """

    REQUIRED_PARAMS = ("metric", "channel", "starttime", "endtime")
    serializer_class = serializers.ArchiveSerializer
    filter_class = ArchiveFilter
    queryset = Archive.objects.all()

    def list(self, request, *args, **kwargs):
        if not all([required_param in request.query_params
           for required_param in self.REQUIRED_PARAMS]):
            raise MissingParameterException

        return super().list(self, request, *args, **kwargs)
