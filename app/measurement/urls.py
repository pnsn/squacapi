from django.urls import path, include
from rest_framework.routers import DefaultRouter

from measurement import views

router = DefaultRouter()
router.register('metrics', views.MetricViewSet, basename='metric')
router.register('measurements', views.MeasurementViewSet,
                basename='measurement')
router.register('thresholds', views.ThresholdViewSet, basename='threshold')
router.register('monitors', views.MonitorViewSet, basename='monitor')
router.register('triggers', views.TriggerViewSet, basename='trigger')
router.register('alerts', views.AlertViewSet, basename='alert')
router.register('archives', views.ArchiveViewSet, basename='archive')

app_name = "measurement"
urlpatterns = [path('', include(router.urls))]
