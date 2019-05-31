from django.urls import path
from nslc import views
app_name = "nslc"
urlpatterns = [
    path('networks/', views.NetworkList.as_view(), name='network-list'),
    path('networks/<int:pk>', views.NetworkDetail.as_view(),
         name='network-detail'),

    path('stations/', views.StationList.as_view(), name='station-list'),
    path('stations/<int:pk>', views.StationDetail.as_view(),
         name='station-detail'),

    path('locations/', views.LocationList.as_view(), name='location-list'),
    path('locations/<int:pk>', views.LocationDetail.as_view(),
         name='location-detail'),

    path('channels/', views.ChannelList.as_view(), name='channel-list'),
    path('channels/<int:pk>', views.ChannelDetail.as_view(),
         name='channel-detail')
]
