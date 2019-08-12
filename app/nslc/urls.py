from django.urls import path, include
from rest_framework.routers import DefaultRouter

from nslc import views

router = DefaultRouter()
router.register('channels', views.ChannelViewSet)
router.register('stations', views.StationViewSet)
router.register('networks', views.NetworkViewSet)
router.register('groups', views.GroupViewSet)
router.register('channelgroups', views.ChannelGroupViewSet)

app_name = "nslc"
urlpatterns = [path('', include(router.urls))]
