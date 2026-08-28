import json
import sys
from pathlib import Path


# Config file
BASE_DIR = Path(__file__).resolve().parent.parent
_config_path = BASE_DIR / 'config/config.json'

if not _config_path.is_file():
    sys.exit(f"Configuration file {_config_path.absolute()} not found")
else:
    print(f"Using configuration file: {_config_path.absolute()}")

try:
    with open(_config_path) as file:
        config = json.loads(file.read())
except json.JSONDecodeError as ex:
    sys.exit(f"Configuration file {_config_path.absolute()} could not be parsed!\n{ex}")

# Basic configuration
URL_PREFIX = config.get('url_prefix', '')
DEBUG = config.get('debug', False)
SECRET_KEY = config['secret_key']
ALLOWED_HOSTS = config['allowed_hosts']
SESSION_COOKIE_PATH = f'/{URL_PREFIX}'
LOGIN_URL = 'admin:login'

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'nested_admin',
    'library.apps.LibraryConfig',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'web.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
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

WSGI_APPLICATION = 'web.wsgi.application'

# Security
if not DEBUG:
    SECURE_SSL_REDIRECT = config.get('use_ssl_redirect', True)
    SECURE_HSTS_SECONDS = 600
    SECURE_HSTS_PRELOAD = True
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

    from .logging import LOGGING_SETTINGS
    LOGGING = LOGGING_SETTINGS

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',},
] if not DEBUG else []

# Email
EMAIL_ENABLED = False
if "server_email" in config:
    DEFAULT_FROM_EMAIL = config['server_email']
    SERVER_EMAIL = config['server_email']
    EMAIL_HOST = config['email_host']
    EMAIL_PORT = config.get('email_port', 25)
    EMAIL_HOST_USER = config['email_host_user']
    EMAIL_HOST_PASSWORD = config['email_host_password']
    EMAIL_USE_TLS = config.get('email_use_tls', True)
    EMAIL_USE_SSL = config.get('email_use_ssl', False)
    EMAIL_ENABLED = True

    _admin_list = config.get('admins', [])
    _admin_list = [tuple(item) for item in _admin_list]
    ADMINS = _admin_list
elif DEBUG:
    # If normal email backend is not configured, print emails to console in debug mode
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
    DEFAULT_FROM_EMAIL = "django@localhost"
    EMAIL_ENABLED = True

# Database
_db_backend = config.get('db_backend', 'mysql')
if _db_backend == 'mysql':
    if 'db_user' not in config or 'db_password' not in config:
        sys.exit(f"Please provide sufficient MySQL connection params (user/password)")

    default_db = {
        'ENGINE': 'django.db.backends.mysql',
        'HOST': config.get('db_host', 'localhost'),
        'PORT': config.get('db_port', '3306'),
        'NAME': config['db_name'],
        'USER': config['db_user'],
        'PASSWORD': config['db_password'],
    }
elif _db_backend == 'sqlite3' or _db_backend == 'sqlite':
    default_db = {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / config['db_name']
    }
else:
    sys.exit(f"DB backend {_db_backend} is not supported")

DATABASES = {'default': default_db}
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Europe/Moscow'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
MEDIA_ROOT = BASE_DIR / config.get('media_root', 'media')
STATIC_ROOT = BASE_DIR / config.get('static_root', 'static')
STATIC_URL = 'static/'
MEDIA_URL = 'media/'
