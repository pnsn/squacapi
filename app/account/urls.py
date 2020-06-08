from django.urls import path, include
from rest_framework.routers import DefaultRouter
from account import views

router = DefaultRouter()

router.register('users', views.AccountUserViewSet)
router.register('accounts', views.AccountViewSet)


app_name = "account"
urlpatterns = [path('', include(router.urls))]
