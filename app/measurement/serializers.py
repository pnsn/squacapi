from rest_framework import serializers
from .models import Metric, Measurement
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
    url = serializers.HyperlinkedIdentityField(
        view_name="measurement:metric-detail"
    )

    class Meta:
        model = Metric
        fields = (
            'id', 'name', 'url', 'description', 'unit', 'created_at',
            'updated_at'
        )
        read_only_fields = ('id',)
