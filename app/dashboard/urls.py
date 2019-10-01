from django.urls import path, include
from rest_framework.routers import DefaultRouter

from dashboard import views

router = DefaultRouter()

router.register('dashboards', views.DashboardViewSet)
router.register('widgettypes', views.WidgetTypeViewSet)
router.register('widgets', views.WidgetViewSet)
app_name = "dashboard"
urlpatterns = [path('', include(router.urls))]
