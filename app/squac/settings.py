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
    'django_filters',
    'rest_framework',
    'rest_framework.authtoken',
    'core',
    'user',
    'nslc',
    'measurement',
    'dashboard',
    'import',
    'corsheaders',
    'debug_toolbar',
    'drf_yasg',
    'django_rest_passwordreset',
]

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
]


CORS_ORIGIN_WHITELIST = [
     'http://localhost:4200',
     'https://squac.pnsn.org'
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

STATIC_URL = BASE_DIR + '/static/'
STATIC_ROOT = os.environ.get('SQUACAPI_STATIC_ROOT')

AUTH_USER_MODEL = 'core.User'

LOGIN_REDIRECT_URL = "/"
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.environ.get('SQUAC_EMAIL_HOST')
EMAIL_PORT = os.environ.get('SQUAC_EMAIL_PORT')

# Fixture directories
FIXTURE_DIRS = (
   BASE_DIR + '/fixtures/',
)

#point login and logout to drf routes
LOGIN_URL = 'rest_framework:login'
LOGOUT_URL = 'rest_framework:logout'


