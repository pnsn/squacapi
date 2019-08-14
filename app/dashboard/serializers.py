# from rest_framework import serializers
# from .models import Widget, WidgetType, MetricParam, Dashboard, Alarm, \
#     Trigger
# from nslc.models import ChannelGroup
# from measurement.models import Metric


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
