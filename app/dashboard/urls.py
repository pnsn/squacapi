from django.urls import path, include
from rest_framework.routers import DefaultRouter

from dashboard import views

router = DefaultRouter()

router.register('dashboards', views.DashboardViewSet, basename='dashboard')
router.register('widgets', views.WidgetViewSet, basename='widget')
app_name = "dashboard"
urlpatterns = [path('', include(router.urls))]
