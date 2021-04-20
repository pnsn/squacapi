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
router.register('hour-archives', views.ArchiveHourViewSet,
                basename='archive-hour')
router.register('day-archives', views.ArchiveDayViewSet,
                basename='archive-day')
router.register('week-archives', views.ArchiveWeekViewSet,
                basename='archive-week')
router.register('month-archives', views.ArchiveMonthViewSet,
                basename='archive-month')
router.register('aggregated', views.AggregatedViewSet,
                basename='aggregated')
app_name = "measurement"
urlpatterns = [path('', include(router.urls))]
