from rest_framework import serializers
from .models import DataSource, Metric, Group, MetricGroup, Threshold, Alarm,\
                    Trigger


class TriggerSerializer(serializers.HyperlinkedModelSerializer):
    alarm = serializers.PrimaryKeyRelatedField(
        queryset=Alarm.objects.all()
    )
    url = serializers.HyperlinkedIdentityField(
        view_name='measurement:trigger-detail'
    )

    class Meta:
        model = Trigger
        fields = (
            'id', 'url', 'count', 'alarm', 'created_at', 'updated_at'
        )
        read_only_fields = ('id',)


class AlarmSerializer(serializers.HyperlinkedModelSerializer):
    triggers = TriggerSerializer(many=True, read_only=True)
    threshold = serializers.PrimaryKeyRelatedField(
        queryset=Threshold.objects.all()
    )
    url = serializers.HyperlinkedIdentityField(
        view_name='measurement:alarm-detail'
    )

    class Meta:
        model = Alarm
        fields = (
            'id', 'name', 'url', 'description', 'period', 'num_period',
            'triggers', 'threshold', 'created_at', 'updated_at'
        )
        read_only_fields = ('id',)


class ThresholdSerializer(serializers.HyperlinkedModelSerializer):
    alarms = AlarmSerializer(many=True, read_only=True)
    metricgroup = serializers.PrimaryKeyRelatedField(
        queryset=MetricGroup.objects.all()
    )
    url = serializers.HyperlinkedIdentityField(
        view_name='measurement:threshold-detail'
    )

    class Meta:
        model = Threshold
        fields = (
            'id', 'name', 'url', 'description', 'min', 'max', 'alarms',
            'metricgroup', 'created_at', 'updated_at'
        )
        read_only_fields = ('id',)


class MetricGroupSerializer(serializers.HyperlinkedModelSerializer):
    thresholds = ThresholdSerializer(many=True, read_only=True)
    group = serializers.PrimaryKeyRelatedField(
        queryset=Group.objects.all()
    )
    metric = serializers.PrimaryKeyRelatedField(
        queryset=Metric.objects.all()
    )
    url = serializers.HyperlinkedIdentityField(
        view_name="measurement:metricgroup-detail"
    )

    class Meta:
        model = MetricGroup
        fields = (
            'id', 'url', 'group', 'metric', 'thresholds', 'created_at',
            'updated_at'
        )
        read_only_fields = ('id',)


class MetricSerializer(serializers.HyperlinkedModelSerializer):
    metricgroup = MetricGroupSerializer(many=True, read_only=True)
    datasource = serializers.PrimaryKeyRelatedField(
        queryset=DataSource.objects.all()
    )
    url = serializers.HyperlinkedIdentityField(
        view_name="measurement:metric-detail"
    )

    class Meta:
        model = Metric
        fields = (
            'id', 'name', 'url', 'description', 'metricgroup', 'datasource',
            'unit', 'created_at', 'updated_at'
        )
        read_only_fields = ('id',)


class GroupSerializer(serializers.HyperlinkedModelSerializer):
    metricgroup = MetricGroupSerializer(many=True, read_only=True)
    url = serializers.HyperlinkedIdentityField(
        view_name='measurement:group-detail'
    )

    class Meta:
        model = Group
        fields = (
            'id', 'name', 'url', 'description', 'metricgroup', 'is_public',
            'created_at', 'updated_at'
        )
        read_only_fields = ('id',)


class DataSourceSerializer(serializers.HyperlinkedModelSerializer):
    metrics = MetricSerializer(many=True, read_only=True)
    url = serializers.HyperlinkedIdentityField(
        view_name="measurement:datasource-detail"
    )

    class Meta:
        model = DataSource
        fields = (
            'id', 'name', 'url', 'description', 'created_at', 'updated_at',
            'metrics'
        )
        read_only_fields = ('id',)
