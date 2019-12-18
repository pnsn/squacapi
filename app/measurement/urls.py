from django.urls import path, include
from rest_framework.routers import DefaultRouter

from measurement import views

router = DefaultRouter()
router.register('metrics', views.MetricViewSet)
# basename required for views with get_queryset ovride
router.register('measurements', views.MeasurementViewSet,
                basename='measurement')
router.register('thresholds', views.ThresholdViewSet)

app_name = "measurement"
urlpatterns = [path('', include(router.urls))]
