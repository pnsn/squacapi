from django.urls import path, include
from rest_framework.routers import DefaultRouter

from measurement import views

router = DefaultRouter()
router.register('metrics', views.MetricViewSet)
router.register('measurements', views.MeasurementViewSet)
router.register('thresholds', views.ThresholdViewSet)
router.register('archives', views.ArchiveViewSet)

app_name = "measurement"
urlpatterns = [path('', include(router.urls))]
