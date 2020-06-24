from django.urls import path, include
from rest_framework.routers import DefaultRouter
from institution import views

router = DefaultRouter()

router.register('users', views.InstitutionUserViewSet)
router.register('institution', views.InstitutionViewSet)


app_name = "institution"
urlpatterns = [path('', include(router.urls))]
