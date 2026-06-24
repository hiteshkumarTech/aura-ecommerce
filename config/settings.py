"""
Django settings for the e-commerce project.

Configuration is environment-driven so the same codebase runs locally
(SQLite, DEBUG on) and in production (Postgres, DEBUG off) without edits.
Copy .env.example to .env and adjust values.
"""
from pathlib import Path
import os

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


def env_bool(key: str, default: bool = False) -> bool:
    return os.getenv(key, str(default)).strip().lower() in {"1", "true", "yes", "on"}


# --- Core security -----------------------------------------------------------
SECRET_KEY = os.getenv(
    "SECRET_KEY",
    # Insecure fallback so the project runs out of the box in development.
    "dev-insecure-key-change-me-in-production",
)
DEBUG = env_bool("DEBUG", True)
ALLOWED_HOSTS = [h.strip() for h in os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",") if h.strip()]
CSRF_TRUSTED_ORIGINS = [o.strip() for o in os.getenv("CSRF_TRUSTED_ORIGINS", "").split(",") if o.strip()]

# --- Applications ------------------------------------------------------------
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize",
    # Local apps
    "store",
    "accounts",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",  # serves static files in production
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

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
                "store.context_processors.cart_summary",  # exposes cart count/total site-wide
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# --- Database ----------------------------------------------------------------
# Defaults to SQLite. Set DATABASE_URL (e.g. postgres://user:pass@host:5432/db)
# to use Postgres in production. Parsing kept dependency-free.
DATABASE_URL = os.getenv("DATABASE_URL", "").strip()
if DATABASE_URL.startswith(("postgres://", "postgresql://")):
    from urllib.parse import urlparse

    url = urlparse(DATABASE_URL)
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": url.path.lstrip("/"),
            "USER": url.username or "",
            "PASSWORD": url.password or "",
            "HOST": url.hostname or "",
            "PORT": str(url.port or ""),
            "CONN_MAX_AGE": 600,
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

# --- Password validation -----------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator", "OPTIONS": {"min_length": 8}},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# --- Internationalization ----------------------------------------------------
LANGUAGE_CODE = "en-us"
TIME_ZONE = os.getenv("TIME_ZONE", "UTC")
USE_I18N = True
USE_TZ = True

# --- Static & media ----------------------------------------------------------
STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    # Hashed+compressed manifest storage requires `collectstatic` to build a
    # manifest, so it's production-only. Dev/tests use the plain storage.
    "staticfiles": {
        "BACKEND": (
            "django.contrib.staticfiles.storage.StaticFilesStorage"
            if DEBUG
            else "whitenoise.storage.CompressedManifestStaticFilesStorage"
        )
    },
}

MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# --- Auth flow ---------------------------------------------------------------
LOGIN_URL = "accounts:login"
LOGIN_REDIRECT_URL = "store:product_list"
LOGOUT_REDIRECT_URL = "store:product_list"

# --- Sessions ----------------------------------------------------------------
# Anonymous carts rely on sessions; keep them for 2 weeks.
SESSION_COOKIE_AGE = 60 * 60 * 24 * 14
SESSION_SAVE_EVERY_REQUEST = False

# --- Messages ----------------------------------------------------------------
from django.contrib.messages import constants as message_constants  # noqa: E402

MESSAGE_TAGS = {message_constants.ERROR: "danger"}  # aligns with CSS alert classes

# --- Production hardening (active only when DEBUG is off) --------------------
if not DEBUG:
    SECURE_SSL_REDIRECT = env_bool("SECURE_SSL_REDIRECT", True)
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = int(os.getenv("SECURE_HSTS_SECONDS", "31536000"))
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = "DENY"

# --- Deployment overrides (appended for Render) ---
import os as _os
_db = _os.getenv("DATABASE_URL", "").strip()
if _db:
    import dj_database_url as _dj
    DATABASES = {"default": _dj.parse(_db, conn_max_age=600)}
try:
    ALLOWED_HOSTS
except NameError:
    ALLOWED_HOSTS = ["localhost", "127.0.0.1"]
try:
    CSRF_TRUSTED_ORIGINS
except NameError:
    CSRF_TRUSTED_ORIGINS = []
_rh = _os.getenv("RENDER_EXTERNAL_HOSTNAME")
if _rh:
    ALLOWED_HOSTS = list(ALLOWED_HOSTS) + [_rh]
    CSRF_TRUSTED_ORIGINS = list(CSRF_TRUSTED_ORIGINS) + ["https://" + _rh]

# --- Cloudinary media storage (only active when CLOUDINARY_URL is set) ---
if _os.getenv("CLOUDINARY_URL"):
    INSTALLED_APPS = list(INSTALLED_APPS) + ["cloudinary", "cloudinary_storage"]
    STORAGES = dict(STORAGES)
    STORAGES["default"] = {"BACKEND": "cloudinary_storage.storage.MediaCloudinaryStorage"}
