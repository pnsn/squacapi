from django.urls import path, include
from rest_framework.routers import DefaultRouter

from nslc import views

router = DefaultRouter()
router.register('channels', views.ChannelViewSet, basename='channel')
router.register('networks', views.NetworkViewSet, basename='network')
router.register('groups', views.GroupViewSet, basename='group')
router.register(
    'matching-rules', views.MatchingRuleViewSet, basename='matching-rule')

app_name = "nslc"
urlpatterns = [path('', include(router.urls))]
