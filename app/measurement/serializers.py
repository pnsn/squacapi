from rest_framework import serializers
from .models import Metric, Measurement, Threshold, Archive
from dashboard.models import Widget
from nslc.models import Channel


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
        # return None if this is a collection
        if isinstance(self.context['request'].data, list):
            return None
        return measurement

    def to_representation(self, instance):
        """Return object. On bulk uploads serializing the entire collection
            to return is a large overhead. Check for None type returned by
            def create()
        """
        if instance is None:
            return None
        return super().to_representation(instance)

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
            'id', 'url', 'metric', 'widget', 'minval', 'maxval', 'created_at',
            'updated_at', 'user_id'
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
