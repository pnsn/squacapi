from django.urls import path, include
from rest_framework.routers import DefaultRouter

from measurement import views

router = DefaultRouter()
router.register('datasource', views.DataSourceViewSet)

app_name = "measurement"
urlpatterns = [path('', include(router.urls))]
