from rest_framework import serializers
from .models import Widget, WidgetType, Dashboard
from nslc.models import Group
from measurement.models import Metric
from measurement.serializers import MetricSerializer


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

    class Meta:
        model = Widget
        fields = (
            'id', 'name', 'dashboard', 'widgettype', 'metrics',
            'created_at', 'updated_at'
        )
        read_only_fields = ('id',)


class DashboardSerializer(serializers.HyperlinkedModelSerializer):
    group = serializers.PrimaryKeyRelatedField(
        queryset=Group.objects.all()
    )

    class Meta:
        model = Dashboard
        fields = (
            'id', 'name', 'group', 'created_at', 'updated_at'
        )
        read_only_fields = ('id',)


class WidgetTypeSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = WidgetType
        fields = (
            'id', 'name', 'type', 'created_at', 'updated_at'
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
            'id', 'name', 'group', 'widgets', 'created_at', 'updated_at'
        )
        read_only_fields = ('id',)


<<<<<<< HEAD
class WidgetTypeSerializer(serializers.HyperlinkedModelSerializer):
=======
class WidgetDetailSerializer(WidgetSerializer):
    dashboard = DashboardSerializer(read_only=True)
    widgettype = WidgetTypeSerializer(read_only=True)
    metrics = MetricSerializer(many=True, read_only=True)
>>>>>>> daa99e54852aa1951005512043b5179e3e762223

    class Meta:
        model = Widget
        fields = (
<<<<<<< HEAD
            'id', 'name', 'type', 'created_at', 'updated_at'
=======
            'id', 'name', 'dashboard', 'widgettype', 'metrics',
            'created_at', 'updated_at'
>>>>>>> daa99e54852aa1951005512043b5179e3e762223
        )
        read_only_fields = ('id',)
