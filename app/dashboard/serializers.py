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
    url = serializers.HyperlinkedIdentityField(
        view_name='dashboard:widget-detail'
    )

    class Meta:
        model = Widget
        fields = (
            'id', 'name', 'url', 'dashboard', 'widget_type', 'metrics',
            'created_at', 'updated_at'
        )
        read_only_fields = ('id',)


class DashboardSerializer(serializers.HyperlinkedModelSerializer):
    group = serializers.PrimaryKeyRelatedField(
        queryset=Group.objects.all()
    )
    widget = WidgetSerializer(many=True, read_only=True)
    url = serializers.HyperlinkedIdentityField(
        view_name='dashboard:dashboard-detail'
    )

    class Meta:
        model = Dashboard
        fields = (
            'id', 'name', 'url', 'group', 'widget', 'created_at', 'updated_at'
        )
        read_only_fields = ('id',)


class Widget_TypeSerializer(serializers.HyperlinkedModelSerializer):
    widget = WidgetSerializer(many=True, read_only=True)
    url = serializers.HyperlinkedIdentityField(
        view_name='dashboard:widget_type-detail'
    )

    class Meta:
        model = Widget_Type
        fields = (
            'id', 'name', 'url', 'type', 'widget', 'created_at', 'updated_at'
        )
        read_only_fields = ('id',)


# class TriggerSerializer(serializers.HyperlinkedModelSerializer):
#     alarm = serializers.PrimaryKeyRelatedField(
#         queryset=Alarm.objects.all()
#     )

#     class Meta:
#         model = Trigger
#         fields = (
#             'id', 'alarm', 'created_at'
#         )
#         read_only_fields = ('id',)


# class AlarmSerializer(serializers.HyperlinkedModelSerializer):
#     triggers = TriggerSerializer(many=True, read_only=True)
#     metric_param = serializers.PrimaryKeyRelatedField(
#         queryset=MetricParam.objects.all()
#     )

#     class Meta:
#         model = Alarm
#         fields = (
#             'id', 'name', 'description', 'period', 'num_period',
#             'triggers', 'threshold', 'created_at', 'updated_at'
#         )
#         read_only_fields = ('id',)


# class ThresholdSerializer(serializers.HyperlinkedModelSerializer):
#     alarms = AlarmSerializer(many=True, read_only=True)
#     metricgroup = serializers.PrimaryKeyRelatedField(
#         queryset=MetricGroup.objects.all()
#     )
#     url = serializers.HyperlinkedIdentityField(
#         view_name='measurement:threshold-detail'
#     )

#     class Meta:
#         model = Threshold
#         fields = (
#             'id', 'name', 'url', 'description', 'min', 'max', 'alarms',
#             'metricgroup', 'created_at', 'updated_at'
#         )
#         read_only_fields = ('id',)
