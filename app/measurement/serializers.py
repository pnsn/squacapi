from rest_framework import serializers
from .models import (Metric, Measurement,
                     Alert, ArchiveHour, ArchiveDay, ArchiveWeek, Monitor,
                     Trigger, ArchiveMonth)
from nslc.models import Channel, Group
from nslc.serializers import GroupSerializer


class BulkMeasurementListSerializer(serializers.ListSerializer):
    '''serializer for bulk creating or updating measurements'''

    def create(self, validated_data):
        result = [Measurement(**item) for item in validated_data]
        Measurement.objects.bulk_update_or_create(
            result,
            ['value', 'endtime', 'user'],
            match_field=['metric', 'channel', 'starttime'])
        return result


class MeasurementSerializer(serializers.ModelSerializer):
    '''serializer for measurements'''
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
            'created_at', 'user'
        )
        read_only_fields = ('id', 'user')
        list_serializer_class = BulkMeasurementListSerializer

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


class AggregatedSerializer(serializers.Serializer):
    '''simple serializer for aggregated response data'''
    metric = serializers.IntegerField()
    channel = serializers.IntegerField()
    mean = serializers.FloatField()
    min = serializers.FloatField()
    max = serializers.FloatField()
    minabs = serializers.FloatField()
    maxabs = serializers.FloatField()
    median = serializers.FloatField()
    stdev = serializers.FloatField()
    p05 = serializers.FloatField()
    p10 = serializers.FloatField()
    p90 = serializers.FloatField()
    p95 = serializers.FloatField()
    num_samps = serializers.IntegerField()
    starttime = serializers.DateTimeField()
    endtime = serializers.DateTimeField()
    latest = serializers.FloatField()


class MetricSerializer(serializers.ModelSerializer):

    class Meta:
        model = Metric
        fields = (
            'id', 'name', 'code', 'description', 'unit', 'created_at',
            'updated_at', 'default_minval', 'default_maxval', 'user',
            'reference_url', 'sample_rate'
        )
        read_only_fields = ('id', 'user')


class MonitorSerializer(serializers.ModelSerializer):

    channel_group = serializers.PrimaryKeyRelatedField(
        queryset=Group.objects.all()
    )

    metric = serializers.PrimaryKeyRelatedField(
        queryset=Metric.objects.all()
    )

    class Meta:
        model = Monitor
        fields = (
            'id', 'channel_group', 'metric', 'interval_type',
            'interval_count', 'stat', 'name', 'created_at', 'updated_at',
            'user'
        )
        read_only_fields = ('id', 'user')


class TriggerSerializer(serializers.ModelSerializer):

    monitor = serializers.PrimaryKeyRelatedField(
        queryset=Monitor.objects.all())

    class Meta:
        model = Trigger
        fields = (
            'id', 'monitor', 'val1', 'val2', 'value_operator',
            'num_channels', 'num_channels_operator', 'email_list',
            'created_at', 'updated_at', 'user', 'alert_on_out_of_alarm'
        )
        read_only_fields = ('id', 'user')


class AlertSerializer(serializers.ModelSerializer):
    trigger = serializers.PrimaryKeyRelatedField(
        queryset=Trigger.objects.all())

    class Meta:
        model = Alert
        fields = (
            'id', 'trigger', 'timestamp', 'message', 'in_alarm',
            'breaching_channels', 'created_at', 'updated_at', 'user'
        )
        read_only_fields = ('id', 'user')


class ArchiveBaseSerializer(serializers.HyperlinkedModelSerializer):
    """converts an Archive into a serialized representation """
    channel = serializers.PrimaryKeyRelatedField(
        queryset=Channel.objects.all())
    metric = serializers.PrimaryKeyRelatedField(
        queryset=Metric.objects.all())
    minabs = serializers.ReadOnlyField()
    maxabs = serializers.ReadOnlyField()


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


class MonitorDetailSerializer(serializers.ModelSerializer):
    channel_group = GroupSerializer(read_only=True)
    metric = MetricSerializer(read_only=True)
    triggers = TriggerSerializer(many=True, read_only=True)

    class Meta:
        model = Monitor
        fields = (
            'id', 'channel_group', 'metric', 'interval_type',
            'interval_count', 'stat', 'name', 'created_at', 'updated_at',
            'user', 'triggers'
        )
        read_only_fields = ('id', 'user')


class AlertDetailSerializer(serializers.ModelSerializer):
    trigger = TriggerSerializer(read_only=True)

    class Meta:
        model = Alert
        fields = (
            'id', 'trigger', 'timestamp', 'message', 'in_alarm',
            'breaching_channels', 'created_at', 'updated_at', 'user'
        )
        read_only_fields = ('id', 'user')
