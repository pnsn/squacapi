from django.urls import path, include
from rest_framework.routers import DefaultRouter

from nslc import views

router = DefaultRouter()
router.register('channels', views.ChannelViewSet)
router.register('locations', views.LocationViewSet)
router.register('stations', views.StationViewSet)
router.register('networks', views.NetworkViewSet)

app_name = "nslc"
urlpatterns = [path('', include(router.urls))]
