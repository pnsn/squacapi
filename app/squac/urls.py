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
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('django.contrib.auth.urls')),
    path('user/', include('user.urls')),
    path('v1.0/nslc/', include('nslc.urls')),
    path('v1.0/measurement/', include('measurement.urls')),
    path('v1.0/widget/', include('dashboard.urls'))
]
'''To access password reset: localhost:8000/acounts/password_reset/
For test reseting password: reset email text file will be created in a
new directory app/sent_emails/(reset email) and link to password reset
form will be found in the email text file'''
