"""
WSGI config for app project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/dev/howto/deployment/wsgi/
"""

import os
import sys
from django.core.wsgi import get_wsgi_application
import dotenv

# there is probably a better way of doing this but without we get the module
# squac not found
# include full path up to app/
APP_ROOT = os.path.join(os.path.dirname(__file__), '..')
# Add to path modules  ../app
sys.path.insert(0, os.path.abspath(APP_ROOT))
# load env variables
dotenv_path = os.path.join(APP_ROOT, '.env')
dotenv.read_dotenv(dotenv_path)
# load settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'squac.settings')

application = get_wsgi_application()
