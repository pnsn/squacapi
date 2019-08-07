from django.urls import path, include
from rest_framework.routers import DefaultRouter

from measurement import views

router = DefaultRouter()
router.register('datasource', views.DataSourceViewSet)
router.register('metric', views.MetricViewSet)
router.register('measurement', views.MeasurementViewSet)
router.register('group', views.GroupViewSet)
router.register('metricgroup', views.MetricGroupViewSet)
router.register('threshold', views.ThresholdViewSet)
router.register('alarm', views.AlarmViewSet)
router.register('trigger', views.TriggerViewSet)

app_name = "measurement"
urlpatterns = [path('', include(router.urls))]
