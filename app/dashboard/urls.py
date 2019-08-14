from django.urls import path, include
from rest_framework.routers import DefaultRouter

from dashboard import views

router = DefaultRouter()

router.register('dashboard', views.DashboardViewSet)
router.register('widget_type', views.Widget_TypeViewSet)
router.register('widget', views.WidgetViewSet)
# router.register('alarm', views.AlarmViewSet)
# router.register('trigger', views.TriggerViewSet)

app_name = "dashboard"
urlpatterns = [path('', include(router.urls))]
