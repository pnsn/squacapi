"""app URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/dev/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from . import views


schema_view = get_schema_view(
    openapi.Info(
        title="Squac API",
        default_version='v1',
        description="API for accessing squac data",
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="contact@snippets.local"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)


urlpatterns = [
    path('', views.home_v1, name='Squacapi V1.0'),
    path('admin/', admin.site.urls),
    path('user/', include('user.urls', namespace='legacy')),
    path('v1.0/user/', include('user.urls')),
    path('v1.0/', views.home_v1, name='Squacapi V1.0'),
    path('v1.0/nslc/', include('nslc.urls')),
    path('v1.0/measurement/', include('measurement.urls')),
    path('v1.0/dashboard/', include('dashboard.urls')),
    # api password reset endpoints
    path('v1.0/password_reset/', include('django_rest_passwordreset.urls',
         namespace='password_reset')),

    # default path for thel login /logout
    path('api-auth/', include('rest_framework.urls',
         namespace='rest_framework')),
    path('swagger/',
         schema_view.with_ui('swagger', cache_timeout=0),
         name='schema-swagger-ui'),
    re_path(r'^swagger(?P<format>\.json|\.yaml)$',
            schema_view.without_ui(cache_timeout=0),
            name='schema-json'),
    # browser routes for password resets
    path('accounts/', include('django.contrib.auth.urls')),
]

if settings.DEBUG:
    import debug_toolbar
    urlpatterns = [
        path('__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns
