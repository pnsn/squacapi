# from rest_framework import viewsets
# from rest_framework.authentication import TokenAuthentication, \
#     SessionAuthentication
# from rest_framework.permissions import BasePermission, SAFE_METHODS

# from .models import DataSource, Metric, Measurement
# from measurement import serializers


# class ThresholdViewSet(BaseMeasurementViewSet):
#     serializer_class = serializers.ThresholdSerializer
#     queryset = Threshold.objects.all()


# class AlarmViewSet(BaseMeasurementViewSet):
#     serializer_class = serializers.AlarmSerializer
#     queryset = Alarm.objects.all()


# class TriggerViewSet(BaseMeasurementViewSet):
#     serializer_class = serializers.TriggerSerializer
#     queryset = Trigger.objects.all()
