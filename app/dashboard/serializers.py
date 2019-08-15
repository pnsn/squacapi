from rest_framework import serializers
from .models import Widget, Widget_Type, Dashboard
from nslc.models import Group
from measurement.models import Metric


class WidgetSerializer(serializers.HyperlinkedModelSerializer):
    dashboard = serializers.PrimaryKeyRelatedField(
        queryset=Dashboard.objects.all()
    )
    widget_type = serializers.PrimaryKeyRelatedField(
        queryset=Widget_Type.objects.all()
    )
    metrics = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Metric.objects.all()
    )

    class Meta:
        model = Widget
        fields = (
            'id', 'name', 'dashboard', 'widget_type', 'metrics',
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


class Widget_TypeSerializer(serializers.HyperlinkedModelSerializer):
    widget = WidgetSerializer(many=True, read_only=True)

    class Meta:
        model = Widget_Type
        fields = (
            'id', 'name', 'type', 'widget', 'created_at', 'updated_at'
        )
        read_only_fields = ('id',)
