from rest_framework import serializers
from .models import Metric, Measurement, Threshold, Archive
from dashboard.models import Widget
from nslc.models import Channel


class MeasurementSerializer(serializers.HyperlinkedModelSerializer):
    metric = serializers.PrimaryKeyRelatedField(
        queryset=Metric.objects.all()
    )
    channel = serializers.PrimaryKeyRelatedField(
        queryset=Channel.objects.all()
    )
    user = serializers.ReadOnlyField(source='user.username')

    class Meta:
        model = Measurement
        fields = (
            'id', 'metric', 'channel', 'value', 'starttime', 'endtime',
            'created_at', 'user'
        )
        read_only_fields = ('id',)

    @staticmethod
    def setup_eager_loading(queryset):
        queryset = queryset.select_related('channel')
        return queryset


class MetricSerializer(serializers.HyperlinkedModelSerializer):
    # commenting this out since we have a valid model attr called url
    # url = serializers.HyperlinkedIdentityField(
    #     view_name="measurement:metric-detail"
    # )
    user = serializers.ReadOnlyField(source='user.username')

    class Meta:
        model = Metric
        fields = (
            'id', 'name', 'code', 'url', 'description', 'unit', 'created_at',
            'updated_at', 'default_minval', 'default_maxval', 'user'
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
    user = serializers.ReadOnlyField(source='user.username')

    class Meta:
        model = Threshold
        fields = (
            'id', 'url', 'metric', 'widget', 'minval', 'maxval', 'created_at',
            'updated_at', 'user'
        )
        read_only_fields = ('id',)


<<<<<<< HEAD
class ArchiveTypeSerializer(serializers.HyperlinkedModelSerializer):
    """converts an Archive type into a serialized representation """
    class Meta:
        model = ArchiveType
        fields = (
            'id', 'name'
        )
        read_only_fields = ('id',)


=======
>>>>>>> 88067efc5cea147a369a798dc077b8a6b3f52e9e
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
