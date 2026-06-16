# configuration/settings/test.py
from .base import *  # noqa

# --- hard off for tests ---
DEBUG = False
SECRET_KEY = "test-secret-key"
ENABLE_LDAP = False

# --- remove LDAP backends no matter what ---
AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
]

# --- remove optional apps that can break test startup ---
INSTALLED_APPS = [
    app
    for app in INSTALLED_APPS
    if app
    not in {
        "django_python3_ldap",
        "django_browser_reload",
    }
]

# --- remove optional middleware that can break test startup ---
MIDDLEWARE = [mw for mw in MIDDLEWARE if not mw.startswith("django_browser_reload.")]

# --- CRITICAL: multi-db projects must drop external DBs for tests unless you really test them ---
# Otherwise Django/pytest may attempt to set up test DBs / connections for them.
DATABASES = {
    "default": DATABASES["default"],
}

# Optional: use an in-memory sqlite db for speed (fine for most test suites)
DATABASES["default"]["NAME"] = ":memory:"

# speed / isolation helpers
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
CACHES = {"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}
