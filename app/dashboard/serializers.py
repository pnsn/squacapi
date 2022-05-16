from rest_framework import serializers
from .models import Widget, Dashboard
from nslc.models import Group
from measurement.models import Metric
from measurement.serializers import ThresholdSerializer, MetricSerializer
from organization.models import Organization


class WidgetSerializer(serializers.HyperlinkedModelSerializer):
    '''Post/PUT serializer'''
    dashboard = serializers.PrimaryKeyRelatedField(
        queryset=Dashboard.objects.all()
    )
    metrics = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Metric.objects.all()
    )
    channel_group = serializers.PrimaryKeyRelatedField(
        queryset=Group.objects.all()
    )

    class Meta:
        model = Widget
        fields = (
            'id', 'name', 'dashboard', 'description', 'metrics',
            'created_at', 'updated_at', 'channel_group', 'user_id', 'layout',
            'properties'
        )
        read_only_fields = ('id',)


class DashboardSerializer(serializers.HyperlinkedModelSerializer):
    organization = serializers.PrimaryKeyRelatedField(
        queryset=Organization.objects.all()
    )

    class Meta:
        model = Dashboard
        fields = (
            'id', 'name', 'description', 'created_at', 'updated_at',
            'user_id', 'share_all', 'share_org', 'organization'
        )
        read_only_fields = ('id',)


class DashboardDetailSerializer(DashboardSerializer):
    widgets = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Widget.objects.all()
    )

    organization = serializers.PrimaryKeyRelatedField(
        queryset=Organization.objects.all()
    )

    class Meta:
        model = Dashboard
        fields = (
            'id', 'description', 'name', 'widgets', 'created_at',
            'updated_at', 'user_id', 'share_all', 'share_org', 'starttime',
            'endtime', 'organization', 'window_seconds', 'archive_stat',
            'archive_type', 'properties',
        )
        read_only_fields = ('id',)


class WidgetDetailSerializer(serializers.HyperlinkedModelSerializer):
    '''Detail and list view'''
    dashboard = serializers.PrimaryKeyRelatedField(
        queryset=Dashboard.objects.all()
    )
    metrics = MetricSerializer(many=True, read_only=True)
    thresholds = ThresholdSerializer(many=True, read_only=True)
    channel_group = serializers.PrimaryKeyRelatedField(
        queryset=Group.objects.all()
    )

    class Meta:
        model = Widget
        fields = (
            'id', 'name', 'dashboard', 'description', 'metrics',
            'created_at', 'updated_at', 'thresholds', 'channel_group',
            'user_id', 'properties', 'layout'
        )
        read_only_fields = ('id',)
