from django.urls import path, include
from rest_framework.routers import DefaultRouter

# from widget import views

router = DefaultRouter()


# router.register('alarm', views.AlarmViewSet)
# router.register('trigger', views.TriggerViewSet)

app_name = "dashboard"
urlpatterns = [path('', include(router.urls))]
