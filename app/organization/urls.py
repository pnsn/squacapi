from django.urls import path, include
from rest_framework.routers import DefaultRouter
from organization import views

router = DefaultRouter()

router.register('organizations', views.OrganizationViewSet,
                basename='organization')

app_name = "organization"
urlpatterns = [path('', include(router.urls))]
