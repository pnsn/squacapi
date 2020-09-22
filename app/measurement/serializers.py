from rest_framework import serializers
from .models import (Metric, Measurement, Threshold, Alarms, AlarmMetric,
                     Archive)
from dashboard.models import Widget
from nslc.models import Channel, Group


class MeasurementSerializer(serializers.ModelSerializer):
    metric = serializers.PrimaryKeyRelatedField(
        queryset=Metric.objects.all()
    )
    channel = serializers.PrimaryKeyRelatedField(
        queryset=Channel.objects.all()
    )

    class Meta:
        model = Measurement
        fields = (
            'id', 'metric', 'channel', 'value', 'starttime', 'endtime',
            'created_at', 'user_id'
        )
        read_only_fields = ('id',)

    def create(self, validated_data):
        measurement, created = Measurement.objects.update_or_create(
            metric=validated_data.get('metric', None),
            channel=validated_data.get('channel', None),
            starttime=validated_data.get('starttime', None),
            defaults={
                'value': validated_data.get('value', None),
                'endtime': validated_data.get('endtime', None),
                'user': validated_data.get('user', None)
            })
        return measurement

    @staticmethod
    def setup_eager_loading(queryset):
        queryset = queryset.select_related('channel')
        return queryset


class MetricSerializer(serializers.HyperlinkedModelSerializer):

    url = serializers.HyperlinkedIdentityField(
        view_name="measurement:metric-detail")

    class Meta:
        model = Metric
        fields = (
            'id', 'name', 'code', 'url', 'description', 'unit', 'created_at',
            'updated_at', 'default_minval', 'default_maxval', 'user_id',
            'reference_url'
        )
        read_only_fields = ('id',)


class ThresholdSerializer(serializers.HyperlinkedModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name="measurement:threshold-detail")

    metric = serializers.PrimaryKeyRelatedField(
        queryset=Metric.objects.all())

    widget = serializers.PrimaryKeyRelatedField(
        queryset=Widget.objects.all()
    )

    class Meta:
        model = Threshold
        fields = (
            'id', 'url', 'metric', 'widget', 'minval', 'maxval',
            'band_inclusive', 'created_at', 'updated_at', 'user_id'
        )
        read_only_fields = ('id',)


class AlarmsSerializer(serializers.HyperlinkedModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name="measurement:alarms-detail")

    channel_group = serializers.PrimaryKeyRelatedField(
        queryset=Group.objects.all()
    )

    class Meta:
        model = Alarms
        fields = (
            'id', 'url', 'channel_group', 'interval_type', 'interval_count',
            'created_at', 'updated_at', 'user_id'
        )
        read_only_fields = ('id',)


class AlarmMetricSerializer(serializers.HyperlinkedModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name="measurement:alarm-metric-detail")

    alarm = serializers.PrimaryKeyRelatedField(
        queryset=Alarms.objects.all())

    metric = serializers.PrimaryKeyRelatedField(
        queryset=Metric.objects.all())

    class Meta:
        model = AlarmMetric
        fields = (
            'id', 'url', 'alarm', 'metric', 'minval', 'maxval',
            'band_inclusive', 'stat', 'weight', 'created_at', 'updated_at',
            'user_id'
        )
        read_only_fields = ('id',)


class ArchiveSerializer(serializers.HyperlinkedModelSerializer):
    """converts an Archive into a serialized representation """
    id = serializers.HyperlinkedIdentityField(
        view_name="measurement:archive-detail", read_only=True)
    channel = serializers.PrimaryKeyRelatedField(
        queryset=Channel.objects.all())
    metric = serializers.PrimaryKeyRelatedField(
        queryset=Metric.objects.all())

    class Meta:
        model = Archive
        exclude = ("url",)
