import os
from pathlib import Path
from decouple import config

BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = config('SECRET_KEY') # IMPORTANT: KEEP YOUR ORIGINAL OR GENERATE A NEW ONE
DEBUG = True
ALLOWED_HOSTS = ['192.168.138.70', '127.0.0.1', '192.168.43.70']
INSTALLED_APPS = [
    'django.contrib.admin', 'django.contrib.auth', 'django.contrib.contenttypes',
    'django.contrib.sessions', 'django.contrib.messages', 'django.contrib.staticfiles',
    'django.contrib.gis', 'rest_framework', 'rest_framework_gis', 'leaflet', 'core',
]
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware', 'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware', 'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware', 'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]
ROOT_URLCONF = 'pms.urls'
TEMPLATES = [{'BACKEND': 'django.template.backends.django.DjangoTemplates', 'DIRS': [BASE_DIR / 'templates'], 'APP_DIRS': True, 'OPTIONS': {'context_processors': ['django.template.context_processors.debug', 'django.template.context_processors.request', 'django.contrib.auth.context_processors.auth', 'django.contrib.messages.context_processors.messages',],},},]
WSGI_APPLICATION = 'pms.wsgi.application'
DATABASES = {'default': {'ENGINE': 'django.contrib.gis.db.backends.postgis', 'NAME': 'geosmartdb', 'USER': 'postgres', 'PASSWORD': config('DB_PASSWORD'), 'HOST': 'localhost', 'PORT': '5432',}} # <-- Enter your password here
AUTH_PASSWORD_VALIDATORS = [{'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',}, {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',}, {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',}, {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',},]
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True  # For security
EMAIL_HOST_USER = 'anandtj06@gmail.com'  
EMAIL_HOST_PASSWORD = config('EMAIL_PASSWORD')
DEFAULT_FROM_EMAIL = 'anandtj06@gmail.com'
LEAFLET_CONFIG = {'DEFAULT_CENTER': (12.9716, 77.5946), 'DEFAULT_ZOOM': 11}

if os.name == 'nt':
    GDAL_LIBRARY_PATH = r'C:\OSGeo4W\bin\gdal311.dll' # <-- Make sure this filename is correct for your PC
    GEOS_LIBRARY_PATH = r'C:\OSGeo4W\bin\geos_c.dll'

    os.environ['GDAL_DATA'] = r'C:\OSGeo4W\share\gdal'
    os.environ['PROJ_LIB'] = r'C:\OSGeo4W\share\proj'