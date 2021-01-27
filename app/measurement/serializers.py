from rest_framework import serializers
from .models import (Metric, Measurement, Threshold,
                     Alert, ArchiveHour, ArchiveDay, ArchiveWeek, Monitor,
                     Trigger, ArchiveMonth)
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

    # @staticmethod
    # def setup_eager_loading(queryset):
    #     queryset = queryset.select_related('channel')
    #     return queryset


class MetricSerializer(serializers.HyperlinkedModelSerializer):

    url = serializers.HyperlinkedIdentityField(
        view_name="measurement:metric-detail")

    class Meta:
        model = Metric
        fields = (
            'id', 'name', 'code', 'url', 'description', 'unit', 'created_at',
            'updated_at', 'default_minval', 'default_maxval', 'user_id',
            'reference_url', 'sample_rate'
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
            'id', 'url', 'metric', 'widget', 'minval', 'maxval', 'created_at',
            'updated_at', 'user_id'
        )
        read_only_fields = ('id',)


class MonitorSerializer(serializers.HyperlinkedModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name="measurement:monitor-detail")

    channel_group = serializers.PrimaryKeyRelatedField(
        queryset=Group.objects.all()
    )

    metric = serializers.PrimaryKeyRelatedField(
        queryset=Metric.objects.all()
    )

    class Meta:
        model = Monitor
        fields = (
            'id', 'url', 'channel_group', 'metric', 'interval_type',
            'interval_count', 'num_channels', 'stat', 'name', 'created_at',
            'updated_at', 'user_id'
        )
        read_only_fields = ('id',)


class TriggerSerializer(serializers.HyperlinkedModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name="measurement:trigger-detail")

    monitor = serializers.PrimaryKeyRelatedField(
        queryset=Monitor.objects.all())

    class Meta:
        model = Trigger
        fields = (
            'id', 'url', 'monitor', 'minval', 'maxval', 'band_inclusive',
            'level', 'created_at', 'updated_at', 'user_id'
        )
        read_only_fields = ('id',)


class AlertSerializer(serializers.HyperlinkedModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name="measurement:alert-detail")

    trigger = serializers.PrimaryKeyRelatedField(
        queryset=Trigger.objects.all())

    class Meta:
        model = Alert
        fields = (
            'id', 'url', 'trigger', 'timestamp', 'message', 'in_alarm',
            'created_at', 'updated_at', 'user_id'
        )
        read_only_fields = ('id',)


class ArchiveBaseSerializer(serializers.HyperlinkedModelSerializer):
    """converts an Archive into a serialized representation """
    channel = serializers.PrimaryKeyRelatedField(
        queryset=Channel.objects.all())
    metric = serializers.PrimaryKeyRelatedField(
        queryset=Metric.objects.all())


class ArchiveHourSerializer(ArchiveBaseSerializer):

    id = serializers.HyperlinkedIdentityField(
        view_name="measurement:archive-hour-detail", read_only=True)

    class Meta:
        model = ArchiveHour
        exclude = ("url",)


class ArchiveDaySerializer(ArchiveBaseSerializer):

    id = serializers.HyperlinkedIdentityField(
        view_name="measurement:archive-day-detail", read_only=True)

    class Meta:
        model = ArchiveDay
        exclude = ("url",)


class ArchiveWeekSerializer(ArchiveBaseSerializer):

    id = serializers.HyperlinkedIdentityField(
        view_name="measurement:archive-week-detail", read_only=True)

    class Meta:
        model = ArchiveWeek
        exclude = ("url",)


class ArchiveMonthSerializer(ArchiveBaseSerializer):
    """converts an Archive into a serialized representation """
    id = serializers.HyperlinkedIdentityField(
        view_name="measurement:archive-month-detail", read_only=True)

    class Meta:
        model = ArchiveMonth
        exclude = ("url",)
