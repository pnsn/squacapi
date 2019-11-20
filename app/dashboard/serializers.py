from rest_framework import serializers
from .models import Widget, WidgetType, Dashboard, StatType
from nslc.models import Group
from measurement.models import Metric
from measurement.serializers import ThresholdSerializer, MetricSerializer


class WidgetSerializer(serializers.HyperlinkedModelSerializer):
    dashboard = serializers.PrimaryKeyRelatedField(
        queryset=Dashboard.objects.all()
    )
    widgettype = serializers.PrimaryKeyRelatedField(
        queryset=WidgetType.objects.all()
    )
    metrics = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Metric.objects.all()
    )
    stattype = serializers.PrimaryKeyRelatedField(
        queryset=StatType.objects.all()
    )

    class Meta:
        model = Widget
        fields = (
            'id', 'name', 'dashboard', 'widgettype', 'description', 'metrics',
            'created_at', 'updated_at', 'stattype', 'columns', 'rows',
            'x_position', 'y_position'
        )
        read_only_fields = ('id',)


class DashboardSerializer(serializers.HyperlinkedModelSerializer):
    group = serializers.PrimaryKeyRelatedField(
        queryset=Group.objects.all()
    )

    class Meta:
        model = Dashboard
        fields = (
            'id', 'name', 'group', 'description', 'created_at', 'updated_at'
        )
        read_only_fields = ('id',)


class WidgetTypeSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = WidgetType
        fields = (
            'id', 'name', 'type', 'description', 'created_at', 'updated_at'
        )
        read_only_fields = ('id',)


class DashboardDetailSerializer(DashboardSerializer):
    widgets = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Widget.objects.all()
    )

    class Meta:
        model = Dashboard
        fields = (
            'id', 'name', 'description', 'group', 'widgets', 'created_at',
            'updated_at'
        )
        read_only_fields = ('id',)


class StatTypeSerializer(WidgetSerializer):

    class Meta:
        model = StatType
        fields = (
            'type', 'name', 'description'
        )


class WidgetDetailSerializer(WidgetSerializer):
    dashboard = DashboardSerializer(read_only=True)
    widgettype = WidgetTypeSerializer(read_only=True)
    metrics = MetricSerializer(many=True, read_only=True)
    stattype = StatTypeSerializer(read_only=True)
    thresholds = ThresholdSerializer(many=True, read_only=True)

    class Meta:
        model = Widget
        fields = (
            'id', 'name', 'dashboard', 'description', 'widgettype', 'metrics',
            'created_at', 'updated_at', 'thresholds', 'columns', 'rows',
            'x_position', 'y_position'
        )
        read_only_fields = ('id',)
