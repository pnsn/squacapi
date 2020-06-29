from django.urls import path, include
from rest_framework.routers import DefaultRouter
from org import views

router = DefaultRouter()

router.register('users', views.OrganizationUserViewSet)
router.register('organizations', views.OrganizationViewSet)


app_name = "org"
urlpatterns = [path('', include(router.urls))]
