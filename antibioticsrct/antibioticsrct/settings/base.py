"""
Django settings for antibioticsrct project.

Generated by 'django-admin startproject' using Django 1.10.5.

For more information on this file, see
https://docs.djangoproject.com/en/1.10/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.10/ref/settings/
"""

import os
import socket
from common import utils

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.10/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = utils.get_env_setting('SECRET_KEY')


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'anymail',
    'antibioticsrct'
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'antibioticsrct.urls'

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s'
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': 'info.log',
            'formatter': 'verbose'
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': True,
        },
        'antibioticsrct': {
            'handlers': ['file', 'console'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
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

WSGI_APPLICATION = 'antibioticsrct.wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.10/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': utils.get_env_setting('DB_NAME'),
        'USER': utils.get_env_setting('DB_USER'),
        'PASSWORD': utils.get_env_setting('DB_PASS'),
        'HOST': utils.get_env_setting('DB_HOST', '127.0.0.1'),
        'CONN_MAX_AGE': 0  # Must be zero, see api/view_utils#db_timeout
    },
}


# Password validation
# https://docs.djangoproject.com/en/1.10/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/1.10/topics/i18n/

LANGUAGE_CODE = 'en-gb'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.10/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR + '/collected_static/'

# Grab host for generating chart images
GRAB_HOST = "https://openprescribing.net"
GRAB_CMD = ('/usr/local/bin/phantomjs ' +
            BASE_DIR +
            '/scripts/grab_chart.js')
PRINT_CMD = ('/usr/local/bin/phantomjs ' +
            BASE_DIR +
            '/scripts/print_letter.js')
DATA_DIR = BASE_DIR + '/data/'

# Mail settings

ANYMAIL = {
    'MAILGUN_API_KEY': utils.get_env_setting('MAILGUN_API_KEY'),
    'MAILGUN_SENDER_DOMAIN': utils.get_env_setting('MAILGUN_SENDER_DOMAIN'),
}

EMAIL_BACKEND = "anymail.backends.mailgun.EmailBackend"
FAX_FROM_EMAIL = "fax@openprescribing.net"
INTERFAX_USER = utils.get_env_setting('INTERFAX_USER')
INTERFAX_PASS = utils.get_env_setting('INTERFAX_PASS')
DEFAULT_FROM_EMAIL = "hello@openprescribing.net"

# When in debug mode, if no test-recipient is specified when sending
# messages, we override the real recipients with these values.  This
# is belt-and-brances to ensure we never send messages to real users
# when testing.
TEST_FAX_TO = '00441865289412'
TEST_EMAIL_TO = 'seb.bacon+test@gmail.com'


# This app queries the maillog model in OP.  When testing or in dev
# mode, we want to create it locally in migrations.  Otherwise, we
# don't.
CREATE_MAILLOG_TABLE = True
