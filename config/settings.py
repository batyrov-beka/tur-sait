"""
IT Travel — Django жөндөөлөрү (settings).

Маанилүү параметрлер чөйрө өзгөрмөлөрүнөн (environment variables) окулат,
ошондуктан ошол эле код компьютериңизде да, серверде да иштейт.
"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


def load_env_file(path):
    """.env файлынан өзгөрмөлөрдү окуйт (KEY=VALUE). Кошумча пакеттин кереги жок."""
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


load_env_file(BASE_DIR / ".env")


def env_bool(name, default=False):
    return os.environ.get(name, str(default)).lower() in ("1", "true", "yes", "on")


# --- Коопсуздук -------------------------------------------------------------
SECRET_KEY = os.environ.get(
    "DJANGO_SECRET_KEY",
    "dev-only-insecure-key-change-me-in-production",
)
DEBUG = env_bool("DJANGO_DEBUG", True)
ALLOWED_HOSTS = [h.strip() for h in os.environ.get("DJANGO_ALLOWED_HOSTS", "127.0.0.1,localhost").split(",") if h.strip()]
CSRF_TRUSTED_ORIGINS = [o.strip() for o in os.environ.get("DJANGO_CSRF_TRUSTED_ORIGINS", "").split(",") if o.strip()]

if not DEBUG:
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# --- Тиркемелер ------------------------------------------------------------
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize",
    # Google менен кирүү
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "allauth.socialaccount.providers.google",
    # биздин тиркемелер
    "tours.apps.ToursConfig",
    "bookings.apps.BookingsConfig",
    "accounts.apps.AccountsConfig",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "allauth.account.middleware.AccountMiddleware",
]

AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",  # админка үчүн логин/сырсөз
    "allauth.account.auth_backends.AuthenticationBackend",
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
                "django.template.context_processors.i18n",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "tours.context_processors.site_info",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# --- Маалымат базасы -------------------------------------------------------
# Демейки: SQLite (эч нерсе орнотуунун кереги жок).
# PostgreSQL үчүн DATABASE_ENGINE=postgresql жана калган DB_* өзгөрмөлөрүн коюңуз.
if os.environ.get("DATABASE_ENGINE") == "postgresql":
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": os.environ.get("DB_NAME", "ittravel"),
            "USER": os.environ.get("DB_USER", "postgres"),
            "PASSWORD": os.environ.get("DB_PASSWORD", ""),
            "HOST": os.environ.get("DB_HOST", "localhost"),
            "PORT": os.environ.get("DB_PORT", "5432"),
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# --- Тилдер (кыргызча + орусча) -------------------------------------------
# Шаблондордогу түпнуска тексттер кыргызча, орусча котормосу locale/ru/ ичинде.
LANGUAGE_CODE = "ky"
LANGUAGES = [
    ("ky", "Кыргызча"),
    ("ru", "Русский"),
]
LOCALE_PATHS = [BASE_DIR / "locale"]
TIME_ZONE = "Asia/Bishkek"
USE_I18N = True
USE_TZ = True

# --- Статикалык жана медиа файлдар ----------------------------------------
STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"
        if not DEBUG
        else "django.contrib.staticfiles.storage.StaticFilesStorage"
    },
}
MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# --- Кирүү / чыгуу ---------------------------------------------------------
LOGIN_URL = "accounts:login"
LOGIN_REDIRECT_URL = "accounts:cabinet"
LOGOUT_REDIRECT_URL = "tours:home"

# --- Google менен кирүү (django-allauth) -----------------------------------
# Google Cloud Console'дон OAuth Client ID алып, .env файлына жазыңыз (README караңыз).
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", "")
GOOGLE_LOGIN_ENABLED = bool(GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET)

SOCIALACCOUNT_PROVIDERS = {
    "google": {
        "APPS": [{"client_id": GOOGLE_CLIENT_ID, "secret": GOOGLE_CLIENT_SECRET, "key": ""}],
        "SCOPE": ["profile", "email"],
        "AUTH_PARAMS": {"access_type": "online", "prompt": "select_account"},
    }
}
SOCIALACCOUNT_LOGIN_ON_GET = True            # баскычты басканда дароо Google'га өтөт
SOCIALACCOUNT_AUTO_SIGNUP = True             # биринчи киргенде аккаунт өзү түзүлөт
SOCIALACCOUNT_EMAIL_AUTHENTICATION = True    # ошол email менен катталган колдонуучуга кошулат
SOCIALACCOUNT_EMAIL_AUTHENTICATION_AUTO_CONNECT = True
SOCIALACCOUNT_STORE_TOKENS = False
ACCOUNT_EMAIL_VERIFICATION = "none"          # Google email'ди өзү текшерген
ACCOUNT_DEFAULT_HTTP_PROTOCOL = "https" if not DEBUG else "http"

# --- Почта -----------------------------------------------------------------
# Иштеп чыгууда каттар терминалга чыгат. Чыныгы почта үчүн EMAIL_* коюңуз.
EMAIL_BACKEND = os.environ.get("EMAIL_BACKEND", "django.core.mail.backends.console.EmailBackend")
EMAIL_HOST = os.environ.get("EMAIL_HOST", "smtp.gmail.com")
EMAIL_PORT = int(os.environ.get("EMAIL_PORT", "587"))
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD", "")
DEFAULT_FROM_EMAIL = os.environ.get("DEFAULT_FROM_EMAIL", "IT Travel <noreply@ittravel.kg>")

# --- Сайттын байланыш маалыматы (футерде көрүнөт) -------------------------
SITE_NAME = "IT Travel"
SITE_CONTACTS = {
    "email": os.environ.get("SITE_EMAIL", "baatyrovbajys@gmail.com"),
    "phone": os.environ.get("SITE_PHONE", "+996 557 631 771"),
    "address_ky": "Ош шаары, Жапалак",
    "address_ru": "г. Ош, Жапалак",
    "whatsapp": os.environ.get("SITE_WHATSAPP", "996557631771"),
}
# Жаңы брондоо келгенде кат жөнөтүлүүчү дарек
BOOKING_NOTIFY_EMAIL = os.environ.get("BOOKING_NOTIFY_EMAIL", SITE_CONTACTS["email"])

# Telegram боту аркылуу жаңы брондоо / билдирүү жөнүндө кабар (милдеттүү эмес)
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")
