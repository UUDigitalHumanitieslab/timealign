"""
Django settings for timealign project.

Generated by 'django-admin startproject' using Django 1.11.13.

For more information on this file, see
https://docs.djangoproject.com/en/1.11/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.11/ref/settings/
"""
import os
from .settings_secret import *

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.11/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'bseaauw*m9wd2_h-&!+73yig@qd$r+th25k%*!79ckbvat)e3j'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True


ALLOWED_HOSTS = []
if DEBUG:
    from subprocess import Popen, PIPE
    hostname = Popen(('hostname'), stdout=PIPE).communicate()[0].decode().strip()
    ALLOWED_HOSTS.append(hostname)
    ALLOWED_HOSTS.append('127.0.0.1')


# Application definition

INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'bootstrap3',
    'ckeditor',
    'ckeditor_uploader',
    'django_filters',
    'django_object_actions',
    'nested_admin',
    'widget_tweaks',
    'perfectextractor_ui',

    'core.apps.CoreConfig',
    'news.apps.NewsConfig',
    'selections.apps.SelectionsConfig',
    'annotations.apps.AnnotationsConfig',
    'stats.apps.StatsConfig',

    'django.contrib.admin',

    'django.contrib.sites',
    'django.contrib.flatpages',
    'reversion'
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.contrib.flatpages.middleware.FlatpageFallbackMiddleware',
]

ROOT_URLCONF = 'timealign.urls'

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

WSGI_APPLICATION = 'timealign.wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.11/ref/settings/#databases

DATABASES = {
    'default': user_db,
}


# Password validation
# https://docs.djangoproject.com/en/1.11/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/1.11/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.11/howto/static-files/

STATIC_URL = '/static/'

LOGIN_REDIRECT_URL = '/timealign/status'


# Flatpages
# https://docs.djangoproject.com/en/1.11/ref/contrib/flatpages/

SITE_ID = 1

# File handling
MEDIA_ROOT = 'media'
MEDIA_URL = '/media/'

CKEDITOR_UPLOAD_PATH = 'news'
CKEDITOR_IMAGE_BACKEND = 'pillow'

# Path to where the PerfectExtractor corpora reside
PE_DATA_PATH = '/opt/corpora/'
