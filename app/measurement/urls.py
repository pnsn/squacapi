from django.urls import path, include
from rest_framework.routers import DefaultRouter

from measurement import views

router = DefaultRouter()
router.register('metrics', views.MetricViewSet, basename='metric')
router.register('measurements', views.MeasurementViewSet,
                basename='measurement')
router.register('thresholds', views.ThresholdViewSet, basename='threshold')
router.register('alarms', views.AlarmViewSet, basename='alarm')
router.register('alarm-thresholds', views.AlarmThresholdViewSet,
                basename='alarm-threshold')
router.register('alerts', views.AlertViewSet, basename='alert')
router.register('archives', views.ArchiveViewSet, basename='archive')

app_name = "measurement"
urlpatterns = [path('', include(router.urls))]
