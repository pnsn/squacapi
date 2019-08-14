from rest_framework import serializers
from .models import DataSource, Metric, Measurement
from nslc.models import Channel


class MeasurementSerializer(serializers.HyperlinkedModelSerializer):
    metric = serializers.PrimaryKeyRelatedField(
        queryset=Metric.objects.all()
    )
    channel = serializers.PrimaryKeyRelatedField(
        queryset=Channel.objects.all()
    )
    url = serializers.HyperlinkedIdentityField(
        view_name="measurement:measurement-detail"
    )

    class Meta:
        model = Measurement
        fields = (
            'id', 'url', 'metric', 'channel', 'value', 'starttime', 'endtime',
            'created_at', 'updated_at'
        )
        read_only_fields = ('id',)


class MetricSerializer(serializers.HyperlinkedModelSerializer):
    datasource = serializers.PrimaryKeyRelatedField(
        queryset=DataSource.objects.all()
    )
    url = serializers.HyperlinkedIdentityField(
        view_name="measurement:metric-detail"
    )

    class Meta:
        model = Metric
        fields = (
            'id', 'name', 'url', 'description', 'datasource',
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
