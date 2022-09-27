from rest_framework import serializers
from .models import Widget, Dashboard
from nslc.models import Group
from measurement.models import Metric
from measurement.serializers import MetricSerializer
from organization.models import Organization


class WidgetSerializer(serializers.ModelSerializer):
    '''Post/PUT serializer'''
    dashboard = serializers.PrimaryKeyRelatedField(
        queryset=Dashboard.objects.all()
    )
    metrics = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Metric.objects.all()
    )

    class Meta:
        model = Widget
        fields = (
            'id', 'name', 'dashboard', 'metrics',
            'user', 'layout',
            'type', 'properties', 'stat', 'thresholds'
        )
        read_only_fields = ('id', 'user')


class DashboardSerializer(serializers.ModelSerializer):
    organization = serializers.PrimaryKeyRelatedField(
        queryset=Organization.objects.all()
    )
    channel_group = serializers.PrimaryKeyRelatedField(
        queryset=Group.objects.all(),
        required=False
    )

    class Meta:
        model = Dashboard
        fields = (
            'id', 'name', 'description', 'channel_group',
            'user', 'share_all', 'share_org', 'organization',
            'properties',
        )
        read_only_fields = ('id', 'user')


class DashboardDetailSerializer(DashboardSerializer):
    widgets = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Widget.objects.all()
    )

    organization = serializers.PrimaryKeyRelatedField(
        queryset=Organization.objects.all()
    )

    channel_group = serializers.PrimaryKeyRelatedField(
        queryset=Group.objects.all(),
        required=False
    )

    class Meta:
        model = Dashboard
        fields = (
            'id', 'description', 'name', 'widgets', 'channel_group',
            'user', 'share_all', 'share_org', 'organization',
            'properties',
        )
        read_only_fields = ('id', 'user')


class WidgetDetailSerializer(WidgetSerializer):
    '''Detail and list view'''
    dashboard = serializers.PrimaryKeyRelatedField(
        queryset=Dashboard.objects.all()
    )
    metrics = MetricSerializer(many=True, read_only=True)

    class Meta:
        model = Widget
        fields = (
            'id', 'name', 'dashboard', 'metrics', 'thresholds',
            'user', 'type', 'stat',
            'properties', 'layout',
        )
        read_only_fields = ('id', 'user')
