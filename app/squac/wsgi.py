"""
WSGI config for app project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/dev/howto/deployment/wsgi/
"""

import os
import sys
# there is probably a better way of doing this but without we get the module 
# squac not found
# include full path up to app/
file_path = os.path.abspath(os.path.dirname(__file__))
file_list = file_path.split("/")
app_path = "/".join(file_list[0:-1])
sys.path.insert(0, os.path.abspath(app_path))


from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'squac.settings')

application = get_wsgi_application()
