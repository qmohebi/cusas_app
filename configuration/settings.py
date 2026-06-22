# configuration/settings/base.py

from __future__ import annotations

import importlib.util
import logging
import os
from pathlib import Path

from environs import Env

env = Env()

BASE_DIR = Path(__file__).resolve().parent.parent
env.read_env(BASE_DIR / ".env")


def env_bool(name: str, default: bool = False) -> bool:
    return str(os.getenv(name, "1" if default else "0")).strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    )


def is_installed(module_name: str) -> bool:
    return importlib.util.find_spec(module_name) is not None


DEBUG = env_bool("DEBUG", default=True)
ENABLE_LDAP = env_bool("ENABLE_LDAP", default=False)

SECRET_KEY = env.str("DJANGO_SECRET_KEY", default="insecure-dev-key-change-me")
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=["127.0.0.1", "localhost"])

DB_NAME = env("DB_NAME")
DB_USERNAME = env("DB_USERNAME")
DB_PASSWORD = env("DB_PASSWORD")
DB_HOST = env("DB_HOST")
DB_PORT = env("PORT")
LDAP_SERVER = env("LDAP_SERVER")
LDAP_SEARCH_BASE = env("LDAP_SEARCH_BASE")
AUTH_LDAP_BIND_PASSWORD = env("LDAP_BIND_PASSWORD")
LDAP_BIND_DN = env("LDAP_BIND_DN")
DOMAIN = env("DOMAIN")
PG_USERNAME = env("PG_USERNAME")
PG_PASSOWRD = env("PG_PASSWORD")
PG_PORT = env("PG_PORT")
PG_DB_NAME = env("PG_DB_NAME")
PG_DB_HOST = env("PG_HOSTNAME")


INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # project apps
    "accounts",
    "mpce_services",
    "library_app",
    "cusas_app.apps.CusasAppConfig",
    # third-party
    "crispy_forms",
    "crispy_bootstrap5",
    "django_select2",
    "django_filters",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    # "django.contrib.auth.middleware.RemoteUserMiddleware",  # only enable if you really use it
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

# Optional dev-only browser reload (only if installed)
if DEBUG:
    MIDDLEWARE += [
        "django_browser_reload.middleware.BrowserReloadMiddleware",
        "debug_toolbar.middleware.DebugToolbarMiddleware",
    ]
    INSTALLED_APPS += ["debug_toolbar", "django_extensions", "django_browser_reload"]


ROOT_URLCONF = "configuration.urls"
WSGI_APPLICATION = "configuration.wsgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "django.template.context_processors.media",
                "mpce_services.context_processors.services_context",
            ],
        },
    },
]


AUTH_USER_MODEL = "accounts.CustomUser"
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/"

# Start with non-LDAP backends only. LDAP will be inserted when enabled.
AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.RemoteUserBackend",
    "django.contrib.auth.backends.ModelBackend",
]

REMOTE_USER_PROTECTED_VIEWS = [
    "staff_only",
]

REMOTE_USER_PROTECTED_PATHS = [
    "/mpce-staff/",
]


DATABASES: dict = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    },
    #     "default": {
    #         "ENGINE": "django.db.backends.postgresql",
    #         "NAME": PG_DB_NAME,
    #         "USER": PG_USERNAME,
    #         "PASSWORD": PG_PASSOWRD,
    #         "HOST": PG_DB_HOST,
    #         "PORT": PG_PORT,
    #         "OPTIONS": {"sslmode": "disable"},
    #     },
}


# Optional SQL Server connection ("equip") – only include if env is present
DB_NAME = env.str("DB_NAME", default="")
DB_USERNAME = env.str("DB_USERNAME", default="")
DB_PASSWORD = env.str("DB_PASSWORD", default="")
DB_HOST = env.str("DB_HOST", default="")
DB_PORT = env.str("DB_PORT", default="1433")

if all([DB_NAME, DB_USERNAME, DB_PASSWORD, DB_HOST]):
    DATABASES["equip"] = {
        "ENGINE": "mssql",
        "NAME": DB_NAME,
        "USER": DB_USERNAME,
        "PASSWORD": DB_PASSWORD,
        "HOST": DB_HOST,
        "PORT": DB_PORT,
        "OPTIONS": {
            "driver": env.str(
                "MSSQL_ODBC_DRIVER", default="ODBC Driver 18 for SQL Server"
            ),
            "extra_params": env.str(
                "MSSQL_EXTRA_PARAMS",
                default="TrustServerCertificate=yes;Encrypt=yes;",
            ),
        },
    }


AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"
    },
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]


LANGUAGE_CODE = "en-gb"
TIME_ZONE = env.str("DJANGO_TIME_ZONE", default="UTC")
USE_I18N = True
USE_TZ = True


STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"


if ENABLE_LDAP:
    import ldap
    from django_auth_ldap.config import GroupOfNamesType, LDAPSearch

    if is_installed("django_python3_ldap"):
        INSTALLED_APPS.append("django_python3_ldap")

    # Put LDAP backend first
    AUTHENTICATION_BACKENDS.insert(0, "django_auth_ldap.backend.LDAPBackend")

    # LDAP logger
    ldap_logger = logging.getLogger("django_auth_ldap")
    ldap_logger.addHandler(logging.StreamHandler())
    ldap_logger.setLevel(logging.DEBUG)

    AUTH_LDAP_SERVER_URI = env.str("LDAP_SERVER")
    AUTH_LDAP_PERMIT_EMPTY_PASSWORD = True
    AUTH_LDAP_START_TLS = env_bool("LDAP_START_TLS", default=False)

    AUTH_LDAP_BIND_DN = env.str("LDAP_BIND_DN", default="")
    AUTH_LDAP_BIND_PASSWORD = env.str("LDAP_BIND_PASSWORD", default="")

    # Searches (keep your existing DNs)
    AUTH_LDAP_USER_SEARCH = LDAPSearch(
        env.str(
            "LDAP_USER_SEARCH_BASE",
            default="OU=St George's,DC=net,DC=stgeorges,DC=nhs,DC=uk",
        ),
        ldap.SCOPE_SUBTREE,
        "(sAMAccountName=%(user)s)",
    )

    AUTH_LDAP_GROUP_SEARCH = LDAPSearch(
        env.str(
            "LDAP_GROUP_SEARCH_BASE",
            default="OU=Medical Physics,OU=Prof & Scientific SC,OU=St George's,DC=net,DC=stgeorges,DC=nhs,DC=uk",
        ),
        ldap.SCOPE_SUBTREE,
        "(objectClass=groupOfNames)",
    )
    AUTH_LDAP_GROUP_TYPE = GroupOfNamesType()

    AUTH_LDAP_CONNECTION_OPTIONS = {
        ldap.OPT_DEBUG_LEVEL: 0,
        ldap.OPT_REFERRALS: 0,
    }

    # If you use django-python3-ldap settings, keep them inside this block too:
    LDAP_AUTH_USER_FIELDS = {
        "username": "sAMAccountName",
        "first_name": "givenName",
        "last_name": "sn",
        "email": "mail",
    }

    AUTH_LDAP_USER_ATTR_MAP = {
        "first_name": "GivenName",
        "last_name": "sn",
        "email": "mail",
        "department": "department",
        "role": "title",
    }

    LDAP_AUTH_OBJECT_CLASS = "user"
    LDAP_AUTH_CONNECTION_USERNAME = None
    LDAP_AUTH_CONNECTION_PASSWORD = None
    LDAP_AUTH_USER_LOOKUP_FIELDS = ("username",)


# LOGGING = {
#     "version": 1,
#     "disable_existing_loggers": False,
#     "handlers": {"console": {"class": "logging.StreamHandler"}},
#     "loggers": {
#         "django_python3_ldap": {"handlers": ["console"], "level": "DEBUG"},
#         # Uncomment if needed:
#         # "django.db.backends": {"handlers": ["console"], "level": "DEBUG"},
#     },
# }


LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {"class": "logging.StreamHandler"},
        "file": {
            "class": "logging.FileHandler",
            "filename": str(BASE_DIR / "django-errors.log"),
        },
    },
    "root": {"handlers": ["console", "file"], "level": "INFO"},
    "loggers": {
        # This is the one that logs unhandled exceptions with full traceback
        "django.request": {
            "handlers": ["console", "file"],
            "level": "ERROR",
            "propagate": False,
        },
    },
}

DEFAULT_QA_INTERVAL_DAYS = 30
CUSAS_ADMIN_PERMISSION = "accounts.manage_profiles"

EMAIL_HOST = env.str("SMTP")
EMAIL_PORT = env.int("SMTP_PORT")
# Project constants

CELERY_BROKER_URL = "redis://127.0.0.1:6379/0"
CELERY_RESULT_BACKEND = "redis://127.0.0.1:6379"


# for production settings
if not DEBUG:
    SECURE_SSL_REDIRECT = env.bool("SECURE_SSL_REDIRECT", default=False)

    SESSION_COOKIE_SECURE = env.bool("SESSION_COOKIE_SECURE", default=False)
    CSRF_COOKIE_SECURE = env.bool("CSRF_COOKIE_SECURE", default=False)

    SECURE_HSTS_SECONDS = env.int("SECURE_HSTS_SECONDS", default=0)
    SECURE_HSTS_INCLUDE_SUBDOMAINS = False
    SECURE_HSTS_PRELOAD = False

    SESSION_COOKIE_AGE = 15 * 60
    SESSION_SAVE_EVERY_REQUEST = True
    SESSION_EXPIRE_AT_BROWSER_CLOSE = True
