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
from drf_yasg.generators import OpenAPISchemaGenerator
from . import views

'''use drf json response for errors rather than default django html'''
handler500 = 'rest_framework.exceptions.server_error'
handler400 = 'rest_framework.exceptions.bad_request'


class APISchemeGenerator(OpenAPISchemaGenerator):
    def get_schema(self, request=None, public=False):
        schema = super().get_schema(request, public)
        schema.base_path = 'api'
        return schema


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
    generator_class=APISchemeGenerator,
    permission_classes=(permissions.IsAuthenticated,),
)


urlpatterns = [
    path('admin/', admin.site.urls),
    path('invite/', include('invite.urls')),
    # browser routes for password resets
    path('api/user/accounts/', include('django.contrib.auth.urls')),
    path('api/user/', include('user.urls')),
    path('api/nslc/', include('nslc.urls')),
    path('api/measurement/', include('measurement.urls')),
    path('api/dashboard/', include('dashboard.urls')),
    path('api/organization/', include('organization.urls')),
    # api password reset endpoints
    path('api/password_reset/', include('django_rest_passwordreset.urls',
         namespace='password_reset')),
    # invitation url
    path('api/', views.home_v1, name='SQUAC Api Root'),
    # default path for thel login /logout
    path('auth/', include('rest_framework.urls',
         namespace='rest_framework')),
    path('api/docs/',
         schema_view.with_ui('swagger', cache_timeout=0),
         name='schema-swagger-ui'),
    re_path(r'^api/swagger(?P<format>\.json|\.yaml)$',
            schema_view.without_ui(cache_timeout=0),
            name='schema-json'),
    path('', views.home_v1, name='SQUAC Api Root'),

]

if settings.DEBUG:
    import debug_toolbar
    urlpatterns = [
        path('__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns
