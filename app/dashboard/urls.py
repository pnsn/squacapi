from django.urls import path, include
from rest_framework.routers import DefaultRouter

from dashboard import views

router = DefaultRouter()

router.register('dashboards', views.DashboardViewSet, basename='dashboard')
router.register('widgettypes', views.WidgetTypeViewSet, basename='widgettype')
router.register('widgets', views.WidgetViewSet, basename='widget')
router.register('stattype', views.StatTypeViewSet, basename='stattype')
app_name = "dashboard"
urlpatterns = [path('', include(router.urls))]
