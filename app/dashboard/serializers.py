from rest_framework import serializers
from .models import Widget, Dashboard
from nslc.models import Group
from measurement.models import Metric
from measurement.serializers import MetricSerializer
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
            'id', 'name', 'dashboard', 'metrics',
            'channel_group', 'user_id', 'layout',
            'type', 'properties', 'stat'
        )
        read_only_fields = ('id',)


class DashboardSerializer(serializers.HyperlinkedModelSerializer):
    organization = serializers.PrimaryKeyRelatedField(
        queryset=Organization.objects.all()
    )

    class Meta:
        model = Dashboard
        fields = (
            'id', 'name', 'description',
            'user_id', 'share_all', 'share_org', 'organization',
            'properties',
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
            'id', 'description', 'name', 'widgets',
            'user_id', 'share_all', 'share_org', 'organization',
            'properties',
        )
        read_only_fields = ('id',)


class WidgetDetailSerializer(serializers.HyperlinkedModelSerializer):
    '''Detail and list view'''
    dashboard = serializers.PrimaryKeyRelatedField(
        queryset=Dashboard.objects.all()
    )
    metrics = MetricSerializer(many=True, read_only=True)

    channel_group = serializers.PrimaryKeyRelatedField(
        queryset=Group.objects.all()
    )

    class Meta:
        model = Widget
        fields = (
            'id', 'name', 'dashboard', 'metrics', 'thresholds',
            'channel_group', 'user_id', 'type', 'stat',
            'properties', 'layout',
        )
        read_only_fields = ('id',)
