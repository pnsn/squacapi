from rest_framework import serializers
from .models import DataSource, Metric, MetricGroup, Threshold


class ThresholdSerializer(serializers.HyperlinkedModelSerializer):
    metricgroup = serializers.PrimaryKeyRelatedField(
        queryset=MetricGroup.objects.all()
    )
    url = serializers.HyperlinkedIdentityField(
        view_name='measurement:threshold-detail'
    )

    class Meta:
        model = Threshold
        fields = (
            'id', 'name', 'url', 'description', 'min', 'max', 'metricgroup',
            'created_at', 'updated_at'
        )
        read_only_fields = ('id',)


class MetricGroupSerializer(serializers.HyperlinkedModelSerializer):
    metric = serializers.PrimaryKeyRelatedField(
        queryset=Metric.objects.all()
    )
    url = serializers.HyperlinkedIdentityField(
        view_name="measurement:metricgroup-detail"
    )

    class Meta:
        model = MetricGroup
        fields = (
            'id', 'name', 'url', 'description', 'is_public', 'metric',
            'created_at', 'updated_at'
        )
        read_only_fields = ('id',)


class MetricSerializer(serializers.HyperlinkedModelSerializer):
    metricgroups = MetricGroupSerializer(many=True, read_only=True)
    datasource = serializers.PrimaryKeyRelatedField(
        queryset=DataSource.objects.all()
    )
    url = serializers.HyperlinkedIdentityField(
        view_name="measurement:metric-detail"
    )

    class Meta:
        model = Metric
        fields = (
            'id', 'name', 'url', 'description', 'metricgroups', 'datasource',
            'unit', 'created_at', 'updated_at'
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
