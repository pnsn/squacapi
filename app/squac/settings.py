"""
env variables config 
    * dev in docker-compose.yml
    * prod app/.env

"""
import requests
from requests.exceptions import RequestException, MissingSchema
import os
from squac.cronjobs import PRODUCTION_CRONJOBS, STAGING_CRONJOBS

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/dev/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('SQUAC_SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get('SQUAC_DEBUG_MODE') == 'True'

CACHE_ENABLED = os.environ.get('SQUAC_CACHE_ENABLED') == 'True'

try:
    ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS_LIST').split(',')
except AttributeError:
    ALLOWED_HOSTS = ['localhost', '127.0.0.1']

# add EC2 ip to allow heath checks
try:
    EC2_IP = requests.get(os.environ.get('INSTANCE_IP_URL')).text
    ALLOWED_HOSTS.append(EC2_IP)
except RequestException or MissingSchema:
    pass

try:
    EC2_IP = requests.get(os.environ.get('META_DATA_IP_URL')).text
    ALLOWED_HOSTS.append(EC2_IP)
except RequestException or MissingSchema:
    pass

# For debug toolbar
INTERNAL_IPS = [
    'localhost',
    '10.0.2.2'
]

CRONJOBS = STAGING_CRONJOBS

# cronjobs
if os.environ.get('SQUAC_ENVIRONMENT') == 'production':
    CRONJOBS = PRODUCTION_CRONJOBS

# tricks to have debug toolbar when developing with docker
if os.environ.get('USE_DOCKER') == 'yes':
    import socket
    ip = socket.gethostbyname(socket.gethostname())
    INTERNAL_IPS += [ip[:-1] + '1']

DEBUG_TOOLBAR_CONFIG = {
    'DISABLE_PANELS': [
        'debug_toolbar.panels.redirects.RedirectsPanel',
    ],
    'SHOW_TEMPLATE_CONTEXT': True,
}

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.postgres',
    'django_extensions',
    'django_rest_passwordreset',
    'django_filters',
    'rest_framework',
    'rest_framework.authtoken',
    'corsheaders',
    'debug_toolbar',
    'drf_yasg',
    'core',
    'user',
    'nslc',
    'measurement',
    'dashboard',
    'organization',
    'invite',
    'django_crontab'
]

# The caching middlewares must be first and last
MIDDLEWARE = [
    'debug_toolbar.middleware.DebugToolbarMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django_cprofile_middleware.middleware.ProfilerMiddleware'
]


CORS_ORIGIN_WHITELIST = [
    'http://localhost:4200',
    'https://squac.pnsn.org',
    'https://staging-squac.pnsn.org'
]

REST_FRAMEWORK = {
    'DEFAULT_FILTER_BACKENDS': (
        'django_filters.rest_framework.DjangoFilterBackend',
    ),
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework.authentication.SessionAuthentication'
    ),
    # 'DEFAULT_PAGINATION_CLASS': 'squac.pagination.OptionalPagination',
    # 'PAGE_SIZE': 100
}

SWAGGER_SETTINGS = {
    'DEFAULT_AUTO_SCHEMA_CLASS': 'squac.doc_generator.ReadWriteAutoSchema',
    'SECURITY_DEFINITIONS': {
        'Token': {
            'type': 'apiKey',
            'name': 'Authorization',
            'in': 'header'
        }
    }
}

ROOT_URLCONF = 'squac.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR + '/templates/'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'squac.wsgi.application'


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'HOST': os.environ.get('SQUAC_DB_HOST'),
        'NAME': os.environ.get('SQUAC_DB_NAME'),
        'USER': os.environ.get('SQUAC_DB_USER'),
        'PASSWORD': os.environ.get('SQUAC_DB_PASS'),
    }
}


# Default primary key field type, new as of Django 3.2
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field
DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'


# Password validation
# https://docs.djangoproject.com/en/dev/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/dev/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/dev/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = os.environ.get('SQUACAPI_STATIC_ROOT')

AUTH_USER_MODEL = 'core.User'

LOGIN_REDIRECT_URL = "/"
# EMAIL_BACKEND='gmailapi_backend.mail.GmailBackend'
EMAIL_BACKEND = os.environ.get('EMAIL_BACKEND')
EMAIL_HOST = os.environ.get('SQUAC_EMAIL_HOST')
EMAIL_PORT = os.environ.get('SQUAC_EMAIL_PORT')
EMAIL_NO_REPLY = os.environ.get('EMAIL_NO_REPLY')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD')
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER')
EMAIL_ADMIN = os.environ.get('EMAIL_ADMIN')
EMAIL_USE_SSL = os.environ.get('EMAIL_USE_SSL')
DEFAULT_FROM_EMAIL = EMAIL_NO_REPLY
SERVER_EMAIL = EMAIL_NO_REPLY


# Fixture directories
FIXTURE_DIRS = (
    BASE_DIR + '/fixtures/',
)

# point login and logout to drf routes
LOGIN_URL = 'rest_framework:login'
LOGOUT_URL = 'rest_framework:logout'

if DEBUG:
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.dummy.DummyCache'
        }
    }
# need to do it this way since we don't want to install redis locally
if CACHE_ENABLED:
    CACHES = {
        'default': {
            'BACKEND': 'django_redis.cache.RedisCache',
            'LOCATION': os.environ.get('CACHE_LOCATION'),
            'OPTIONS': {
                'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            },
            'TIMEOUT': int(os.environ.get('CACHE_SECONDS')),
            'KEY_PREFIX': 'squac_' + os.environ.get('CACHE_BACKEND')
        }
    }

# FIXME this is broken cache key is not being set
# CACHE_MIDDLEWARE_ALIAS = os.environ.get('CACHE_BACKEND')
# CACHE_MIDDLEWARE_SECONDS = int(os.environ.get('CACHE_SECONDS'))
# CACHE_MIDDLEWARE_KEY_PREFIX = 'squac_' + os.environ.get('CACHE_BACKEND')
# # this is where we specify the CACHES key from above
# SESSION_CACHE_ALIAS = os.environ.get('CACHE_KEY')

NSLC_DEFAULT_CACHE = 60 * 60 * 6

# number of hours to expire invite token
INVITE_TOKEN_EXPIRY_TIME = 48


ADMINS = (
    ('KM', 'marczk@uw.edu '), ('AH', 'ahutko@uw.edu '),
    ('CU', 'ulbergc@uw.edu ')
)
AWS_DEFAULT_REGION = os.environ.get('AWS_DEFAULT_REGION')
AWS_SNS_ADMIN_ARN = os.environ.get('AWS_SNS_ADMIN_ARN')
SQUAC_MEASUREMENTS_BUCKET = os.environ.get('SQUAC_MEASUREMENTS_BUCKET')

MANAGERS = ADMINS

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'simple': {
            'format': '{levelname} {asctime}: {lineno} {message}',
            'style': '{',
        },
    },
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse',
        },
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue',
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'filters': ['require_debug_true'],
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
        'console_on_not_debug': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
        'django.server': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler'
        },
        'null': {  # this
            'level': 'DEBUG',
            'class': 'logging.NullHandler',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'mail_admins', 'console_on_not_debug'],
            'level': "INFO"
        },
        'django.security.DisallowedHost': {  # and this
            'handlers': ['console_on_not_debug'],
            'propagate': False,
        },
        'django.server': {
            'handlers': ['django.server'],
        },
    }
}
