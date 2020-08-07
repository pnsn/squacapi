"""
env variables config 
    * dev in docker-compose.yml
    * prod app/.env

"""

import os

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/dev/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('SQUAC_SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get('SQUAC_DEBUG_MODE') == 'True',

ALLOWED_HOSTS = ['squac.pnsn.org', 'squacapi.pnsn.org', 
                 'localhost', 'staging-squacapi.pnsn.org',
                 'staging-squacapi.pnsn.org']

# For debug toolbar
INTERNAL_IPS = [
    'localhost',
    '10.0.2.2',
]

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
    'django_extensions',
    'django_rest_passwordreset',
    'django_filters',
    'rest_framework',
    'rest_framework.authtoken',
    'gmailapi_backend',
    'corsheaders',
    'debug_toolbar',
    'drf_yasg',
    'core',
    'user',
    'nslc',
    'measurement',
    'dashboard',
    # wtf? 'import',
    'organization',
    'invite',
    
]

# The caching middlewares must be first and last
MIDDLEWARE = [
    'django.middleware.cache.UpdateCacheMiddleware', #must be first
    'debug_toolbar.middleware.DebugToolbarMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.cache.FetchFromCacheMiddleware', #must be last!!

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
     )
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
EMAIL_NO_REPLY=os.environ.get('EMAIL_NO_REPLY')

GMAIL_API_CLIENT_ID = os.environ.get('GMAIL_API_CLIENT_ID')
GMAIL_API_CLIENT_SECRET = os.environ.get('GMAIL_API_CLIENT_SECRET')
GMAIL_API_REFRESH_TOKEN = os.environ.get('GMAIL_API_REFRESH_TOKEN')


# Fixture directories
FIXTURE_DIRS = (
   BASE_DIR + '/fixtures/',
)

#point login and logout to drf routes
LOGIN_URL = 'rest_framework:login'
LOGOUT_URL = 'rest_framework:logout'




CACHES = { 
    'default': { 
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache'
    }
}
# need to do it this way since we don't want to install redis locally
if not DEBUG:   
    CACHES['staging'] = { 
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': os.environ.get('CACHE_LOCATION'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }

    CACHES['production'] = { 
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': os.environ.get('CACHE_LOCATION'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }

# FIXME this is broken cache key is not being set
#CACHE_MIDDLEWARE_ALIAS = os.environ.get('CACHE_BACKEND')	
CACHE_MIDDLEWARE_SECONDS = int(os.environ.get('CACHE_SECONDS'))
CACHE_MIDDLEWARE_KEY_PREFIX='squac_' + os.environ.get('CACHE_BACKEND')

# number of hours to expire invite token
INVITE_TOKEN_EXPIRY_TIME = 48
NO_REPLY_EMAIL="pnsn-no-reply@monitor.ess.washington.edu"

ADMINS = (
  ('JC', 'joncon@uw.edu'),
)

MANAGERS = ADMINS

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
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
            'formatter': 'simple'
        },
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler'
        },
    },
   
    'root': {
        'handlers': ['console'],
        'level': 'WARNING',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'propagate': False,
            'level': os.getenv('DJANGO_LOG_LEVEL', 'INFO'),
        },
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': False,
        }
    }
}