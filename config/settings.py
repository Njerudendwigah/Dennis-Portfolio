"""
Django settings for the Dennis Ndwigah portfolio project.

This settings module supports:
- Local development with SQLite and console email.
- A production deployment driven by environment variables.
- A public portfolio plus a private employer document-access portal.

Alignment notes
---------------
* ``PRIVATE_DOCUMENTS_ROOT`` is read by ``employer_portal.models`` at
  import time — it must be defined before any model module is loaded.
* ``config.urls`` mounts ``employer_portal.urls`` at ``/employer/``.
  Every external portal URL begins with that prefix:

      /employer/login/
      /employer/logout/
      /employer/request-access/
      /employer/request-access/submitted/<uuid>/
      /employer/request-status/<uuid>/
      /employer/portal/<uuid>/
      /employer/staff/dashboard/
      /employer/staff/requests/<uuid>/
      /employer/staff/requests/<uuid>/approve/
      /employer/staff/requests/<uuid>/reject/
      /employer/staff/requests/<uuid>/revoke/

* ``LOGIN_URL`` points at the portal's own themed login page
  (``employer_portal:login``), served by ``StaffAuthenticationForm``.
  The Unfold admin login at ``/admin/login/`` remains functional and
  shares the same session.
* ``LOGIN_REDIRECT_URL`` targets the staff dashboard at
  ``/employer/staff/dashboard/``.
* ``TRUST_X_FORWARDED_FOR`` is consumed by ``client_ip()`` in
  ``employer_portal.models`` and honoured by the audit pipeline.
"""

import os
from pathlib import Path

from django.urls import reverse_lazy


# ---------------------------------------------------------------------------
# BASE
# ---------------------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent


# ---------------------------------------------------------------------------
# ENVIRONMENT HELPERS
# ---------------------------------------------------------------------------


def env_bool(name: str, default: bool = False) -> bool:
    """Read a boolean environment variable safely."""
    value = os.environ.get(name)
    if value is None:
        return default

    return value.strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def env_int(name: str, default: int) -> int:
    """Read an integer environment variable safely."""
    value = os.environ.get(name)
    if value is None or value == "":
        return default
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise RuntimeError(
            f"{name} must be an integer, got {value!r}."
        ) from exc


def env_list(name: str, default: str = "") -> list[str]:
    """Read a comma-separated environment variable into a clean list."""
    return [
        item.strip()
        for item in os.environ.get(name, default).split(",")
        if item.strip()
    ]


# ---------------------------------------------------------------------------
# SECURITY
# ---------------------------------------------------------------------------

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY")
DEBUG = env_bool("DJANGO_DEBUG", True)

if not DEBUG and not SECRET_KEY:
    raise RuntimeError(
        "DJANGO_SECRET_KEY must be set when DJANGO_DEBUG=False."
    )

# Development-only fallback. A real secret is required in production.
SECRET_KEY = SECRET_KEY or (
    "django-insecure-development-only-change-before-production"
)

ALLOWED_HOSTS = env_list(
    "DJANGO_ALLOWED_HOSTS",
    "127.0.0.1,localhost",
)

if not DEBUG and not ALLOWED_HOSTS:
    raise RuntimeError(
        "DJANGO_ALLOWED_HOSTS must contain at least one host when "
        "DJANGO_DEBUG=False."
    )

# Explicitly trust the local Django origins used during development.
# Production deployments should provide the real HTTPS origins through
# DJANGO_CSRF_TRUSTED_ORIGINS.
_csrf_default_origins = (
    "http://127.0.0.1:8000,http://localhost:8000"
    if DEBUG
    else ""
)

CSRF_TRUSTED_ORIGINS = env_list(
    "DJANGO_CSRF_TRUSTED_ORIGINS",
    _csrf_default_origins,
)

# The application only trusts X-Forwarded-For when explicitly configured
# for a trusted reverse proxy. This is consumed by
# ``AccessLog.log_from_request()`` via ``employer_portal.models.client_ip()``.
TRUST_X_FORWARDED_FOR = env_bool(
    "DJANGO_TRUST_X_FORWARDED_FOR",
    False,
)

# Set this only when the reverse proxy terminates TLS and forwards the
# HTTPS scheme using the standard X-Forwarded-Proto header.
USE_SECURE_PROXY_HEADER = env_bool(
    "DJANGO_USE_SECURE_PROXY_HEADER",
    False,
)

if USE_SECURE_PROXY_HEADER:
    SECURE_PROXY_SSL_HEADER = (
        "HTTP_X_FORWARDED_PROTO",
        "https",
    )

# In production, an explicit CSRF trusted-origin list is required so that
# deployments do not accidentally rely on local development defaults.
if not DEBUG and not CSRF_TRUSTED_ORIGINS:
    raise RuntimeError(
        "DJANGO_CSRF_TRUSTED_ORIGINS must contain at least one HTTPS origin "
        "when DJANGO_DEBUG=False."
    )


# ---------------------------------------------------------------------------
# APPLICATIONS
# ---------------------------------------------------------------------------

INSTALLED_APPS = [
    # Unfold admin theme. Must be listed BEFORE django.contrib.admin.
    "unfold",
    "unfold.contrib.filters",
    "unfold.contrib.forms",     # themed widgets used by UserAdmin / forms

    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize",  # naturaltime / intcomma for templates

    # Portfolio employer-access system.
    "employer_portal.apps.EmployerPortalConfig",
]


# ---------------------------------------------------------------------------
# ADMIN THEME (UNFOLD)
# ---------------------------------------------------------------------------

UNFOLD = {
    "SITE_TITLE": "Employer Access Portal",
    "SITE_HEADER": "Employer Access Portal",
    "SITE_SUBHEADER": "Dennis Ndwigah",
    "SITE_URL": "/",
    "SITE_SYMBOL": "badge",
    "SHOW_HISTORY": True,
    "SHOW_VIEW_ON_SITE": True,
    "SHOW_BACK_BUTTON": True,

    # Dashboard callbacks — see employer_portal/dashboard.py.
    "ENVIRONMENT": "employer_portal.dashboard.environment_callback",
    "DASHBOARD_CALLBACK": "employer_portal.dashboard.dashboard_callback",

    "COMMAND": {"search_models": True, "show_history": True},

    "COLORS": {
        # Teal, to match the portfolio and the staff review dashboard.
        "primary": {
            "50": "oklch(98.4% .014 180.72)",
            "100": "oklch(95.3% .051 180.801)",
            "200": "oklch(91% .096 180.426)",
            "300": "oklch(85.5% .138 181.071)",
            "400": "oklch(77.7% .152 181.912)",
            "500": "oklch(70.4% .14 182.503)",
            "600": "oklch(60% .118 184.704)",
            "700": "oklch(51.1% .096 186.391)",
            "800": "oklch(43.7% .078 188.216)",
            "900": "oklch(38.6% .063 188.416)",
            "950": "oklch(27.7% .046 192.524)",
        },
    },

    "SIDEBAR": {
        "show_search": True,
        "show_all_applications": False,
        "navigation": [
            {
                "title": "Overview",
                "separator": False,
                "items": [
                    {
                        "title": "Admin index",
                        "icon": "dashboard",
                        "link": reverse_lazy("admin:index"),
                    },
                    {
                        # Deep-links to the staff dashboard, mounted at
                        # /employer/staff/dashboard/ via config.urls.
                        "title": "Staff dashboard",
                        "icon": "space_dashboard",
                        "link": reverse_lazy(
                            "employer_portal:staff_dashboard"
                        ),
                    },
                ],
            },
            {
                "title": "Access control",
                "separator": True,
                "items": [
                    {
                        "title": "Access requests",
                        "icon": "inbox",
                        "link": reverse_lazy(
                            "admin:employer_portal_accessrequest_changelist"
                        ),
                        "badge": (
                            "employer_portal.dashboard.pending_requests_badge"
                        ),
                        "badge_variant": "warning",
                    },
                    {
                        "title": "Access grants",
                        "icon": "key",
                        "link": reverse_lazy(
                            "admin:employer_portal_accessgrant_changelist"
                        ),
                    },
                    {
                        "title": "Access logs",
                        "icon": "fact_check",
                        "link": reverse_lazy(
                            "admin:employer_portal_accesslog_changelist"
                        ),
                    },
                ],
            },
            {
                "title": "Portfolio content",
                "separator": True,
                "items": [
                    {
                        "title": "Documents",
                        "icon": "description",
                        "link": reverse_lazy(
                            "admin:employer_portal_document_changelist"
                        ),
                    },
                    {
                        "title": "Referees",
                        "icon": "supervisor_account",
                        "link": reverse_lazy(
                            "admin:employer_portal_referee_changelist"
                        ),
                    },
                    {
                        "title": "Employers",
                        "icon": "apartment",
                        "link": reverse_lazy(
                            "admin:employer_portal_employer_changelist"
                        ),
                    },
                ],
            },
            {
                "title": "System",
                "separator": True,
                "items": [
                    {
                        "title": "Users",
                        "icon": "person",
                        "link": reverse_lazy("admin:auth_user_changelist"),
                    },
                    {
                        "title": "Groups",
                        "icon": "group",
                        "link": reverse_lazy("admin:auth_group_changelist"),
                    },
                ],
            },
        ],
    },
}


# ---------------------------------------------------------------------------
# MIDDLEWARE
# ---------------------------------------------------------------------------

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",

    # Must run before CsrfViewMiddleware so the local-only Origin
    # normalisation can handle browser contexts that submit Origin: null.
    "employer_portal.middleware.LocalDevelopmentOriginMiddleware",

    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]


# ---------------------------------------------------------------------------
# URL / APPLICATION SERVER
# ---------------------------------------------------------------------------

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"


# ---------------------------------------------------------------------------
# TEMPLATES
# ---------------------------------------------------------------------------

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]


# ---------------------------------------------------------------------------
# DATABASE
# ---------------------------------------------------------------------------

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}


# ---------------------------------------------------------------------------
# AUTHENTICATION
#
# Staff log in through the portal's themed login page, mounted by
# config.urls at /employer/login/ and named employer_portal:login. The
# stock Unfold login at /admin/login/ remains available and shares the
# same session cookie.
#
# After authentication, staff land on the staff dashboard served by
# employer_portal.views.staff_dashboard at /employer/staff/dashboard/.
#
# These three values MUST match the mount point in config.urls:
#     path("employer/", include("employer_portal.urls")),
# ---------------------------------------------------------------------------

LOGIN_URL = "/employer/login/"
LOGIN_REDIRECT_URL = "/employer/staff/dashboard/"
LOGOUT_REDIRECT_URL = "/"


# ---------------------------------------------------------------------------
# PASSWORD VALIDATION
# ---------------------------------------------------------------------------

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "UserAttributeSimilarityValidator"
        ),
    },
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "MinimumLengthValidator"
        ),
    },
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "CommonPasswordValidator"
        ),
    },
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "NumericPasswordValidator"
        ),
    },
]


# ---------------------------------------------------------------------------
# INTERNATIONALIZATION
# ---------------------------------------------------------------------------

LANGUAGE_CODE = "en-gb"
TIME_ZONE = "Africa/Nairobi"
USE_I18N = True
USE_TZ = True


# ---------------------------------------------------------------------------
# STATIC FILES
# ---------------------------------------------------------------------------

STATIC_URL = "/static/"

# The project-level ``static`` folder holds the employer portal assets at
# static/employer_portal/portal.css and static/employer_portal/portal.js,
# which templates reference as /static/employer_portal/... The portfolio's
# own css, js and images folders remain registered alongside it.
STATICFILES_DIRS = [
    BASE_DIR / "static",
    BASE_DIR / "css",
    BASE_DIR / "js",
    BASE_DIR / "images",
]
STATIC_ROOT = BASE_DIR / "staticfiles"

# Django 4.2+ reads static-file storage exclusively from STORAGES. The
# legacy STATICFILES_STORAGE setting is deprecated and ignored by Django 5+.
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": (
            "django.contrib.staticfiles.storage.StaticFilesStorage"
            if DEBUG
            else (
                "django.contrib.staticfiles.storage."
                "ManifestStaticFilesStorage"
            )
        ),
    },
}


# ---------------------------------------------------------------------------
# MEDIA / PRIVATE DOCUMENT STORAGE
# ---------------------------------------------------------------------------

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# Do not expose this directory through MEDIA_URL. Employer documents are
# served only through controlled Django views after grant validation.
# employer_portal.models.PrivateDocumentStorage reads this setting at
# import time — it must be defined before any model module is loaded.
PRIVATE_DOCUMENTS_ROOT = BASE_DIR / "private" / "documents"


# ---------------------------------------------------------------------------
# FILE UPLOAD LIMITS
# ---------------------------------------------------------------------------

FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024
DATA_UPLOAD_MAX_MEMORY_SIZE = 25 * 1024 * 1024


# ---------------------------------------------------------------------------
# EMAIL
# ---------------------------------------------------------------------------

# Development uses console email so submissions can be tested without
# sending real messages. Production uses SMTP through environment variables.
if DEBUG:
    EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
else:
    EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"

EMAIL_HOST = os.environ.get("EMAIL_HOST", "").strip()
EMAIL_PORT = env_int("EMAIL_PORT", 587)
EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER", "").strip()
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD", "")
EMAIL_USE_TLS = env_bool("EMAIL_USE_TLS", True)
EMAIL_USE_SSL = env_bool("EMAIL_USE_SSL", False)
EMAIL_TIMEOUT = env_int("EMAIL_TIMEOUT", 20)

if EMAIL_USE_TLS and EMAIL_USE_SSL:
    raise RuntimeError(
        "EMAIL_USE_TLS and EMAIL_USE_SSL cannot both be enabled."
    )

if not 1 <= EMAIL_PORT <= 65535:
    raise RuntimeError(
        "EMAIL_PORT must be between 1 and 65535."
    )

if EMAIL_TIMEOUT <= 0:
    raise RuntimeError(
        "EMAIL_TIMEOUT must be greater than zero."
    )

if not DEBUG and not EMAIL_HOST:
    raise RuntimeError(
        "EMAIL_HOST must be set when DJANGO_DEBUG=False."
    )

DEFAULT_FROM_EMAIL = os.environ.get(
    "DEFAULT_FROM_EMAIL",
    "Dennis Ndwigah <dennisndwigah.dn.dn@gmail.com>",
)

SERVER_EMAIL = os.environ.get(
    "SERVER_EMAIL",
    "dennisndwigah.dn.dn@gmail.com",
)

EMPLOYER_NOTIFICATION_EMAIL = os.environ.get(
    "EMPLOYER_NOTIFICATION_EMAIL",
    "dennisndwigah.dn.dn@gmail.com",
)

# In production, fail fast when employer notifications are not configured.
# This prevents a deployment from appearing operational while silently
# dropping access-request notifications.
if not DEBUG and not EMPLOYER_NOTIFICATION_EMAIL:
    raise RuntimeError(
        "EMPLOYER_NOTIFICATION_EMAIL must be set when DJANGO_DEBUG=False."
    )


# ---------------------------------------------------------------------------
# SESSION / COOKIE SECURITY
# ---------------------------------------------------------------------------

SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_SECURE = not DEBUG
SESSION_COOKIE_AGE = env_int("DJANGO_SESSION_COOKIE_AGE", 28800)

if SESSION_COOKIE_AGE <= 0:
    raise RuntimeError(
        "DJANGO_SESSION_COOKIE_AGE must be greater than zero."
    )

# Django needs client-side access to the CSRF cookie for the standard
# middleware flow used by the current templates.
CSRF_COOKIE_HTTPONLY = False
CSRF_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SECURE = not DEBUG


# ---------------------------------------------------------------------------
# PRODUCTION SECURITY HEADERS
# ---------------------------------------------------------------------------

SECURE_SSL_REDIRECT = env_bool(
    "DJANGO_SECURE_SSL_REDIRECT",
    not DEBUG,
)

SECURE_HSTS_SECONDS = env_int(
    "DJANGO_HSTS_SECONDS",
    31536000 if not DEBUG else 0,
)
SECURE_HSTS_INCLUDE_SUBDOMAINS = env_bool(
    "DJANGO_HSTS_INCLUDE_SUBDOMAINS",
    False,
)
SECURE_HSTS_PRELOAD = env_bool(
    "DJANGO_HSTS_PRELOAD",
    False,
)
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"
SECURE_CROSS_ORIGIN_OPENER_POLICY = "same-origin"
X_FRAME_OPTIONS = "DENY"

if SECURE_HSTS_SECONDS < 0:
    raise RuntimeError(
        "DJANGO_HSTS_SECONDS cannot be negative."
    )

if SECURE_HSTS_PRELOAD and SECURE_HSTS_SECONDS < 31536000:
    raise RuntimeError(
        "DJANGO_HSTS_PRELOAD requires at least 31536000 seconds of HSTS."
    )

# Proxy headers are trusted only when the deployment explicitly enables
# the corresponding setting above. X-Forwarded-For is handled independently
# by the employer portal through TRUST_X_FORWARDED_FOR.


# ---------------------------------------------------------------------------
# DEFAULT PRIMARY KEY
# ---------------------------------------------------------------------------

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"