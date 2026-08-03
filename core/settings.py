"""
Django settings for core project.
Konfigurasi ini mendukung:
- Development lokal: SQLite (default, jika DATABASE_URL tidak di-set)
- Production (Supabase/Railway/Render): PostgreSQL via DATABASE_URL env var

Setup untuk Supabase:
1. Salin .env.example ke .env
2. Isi DATABASE_URL dengan connection string dari Supabase > Settings > Database > Connection string (URI mode)
   Format: postgresql://postgres.[PROJECT-REF]:[PASSWORD]@aws-0-[REGION].pooler.supabase.com:6543/postgres
3. Jalankan: python manage.py migrate
"""

import os
from pathlib import Path
import dj_database_url
from decouple import config

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# ============================================================
# SECURITY
# ============================================================
SECRET_KEY = config('SECRET_KEY', default='django-insecure-3tk8cvxw5z0yshu!k-*4pcj_=cu-lt6nm*xtmku)@jgjqks1qp')
DEBUG = config('DEBUG', default=True, cast=bool)

# Parse ALLOWED_HOSTS dari env var (comma-separated)
_raw_hosts = config('ALLOWED_HOSTS', default='127.0.0.1,localhost')
ALLOWED_HOSTS = [h.strip() for h in _raw_hosts.split(',') if h.strip()]
ALLOWED_HOSTS.extend(['.vercel.app', 'srs-generator-tools.vercel.app'])

# ============================================================
# INSTALLED APPS
# ============================================================
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'main',
]

# ============================================================
# MIDDLEWARE
# ============================================================
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # Serve static files di production
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'core.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'core.wsgi.application'

# ============================================================
# DATABASE
# Auto-detect: SQLite di dev, PostgreSQL di production.
#
# Untuk pakai Supabase / PostgreSQL, set env var:
#   DATABASE_URL=postgresql://postgres.[ref]:[pass]@aws-0-[region].pooler.supabase.com:6543/postgres
#
# JANGAN set DATABASE_URL jika ingin pakai SQLite lokal.
# ============================================================
_DATABASE_URL = config('DATABASE_URL', default=f'sqlite:///{BASE_DIR / "db.sqlite3"}')

_is_postgres = _DATABASE_URL.startswith('postgres')

DATABASES = {
    'default': dj_database_url.parse(
        _DATABASE_URL,
        # Karena menggunakan Supabase Connection Pooler (Port 6543 - Transaction Mode),
        # conn_max_age HARUS 0 agar Django tidak bentrok dengan pooling dari Supavisor.
        conn_max_age=0,
        conn_health_checks=_is_postgres,
    )
}

# Khusus SQLite: tambahkan timeout agar tidak error saat concurrent access
if not _is_postgres:
    DATABASES['default'].setdefault('OPTIONS', {})
    DATABASES['default']['OPTIONS']['timeout'] = 60

# Khusus PostgreSQL:
# JANGAN gunakan server_side_binding=True saat menggunakan pooler di mode transaction (port 6543),
# karena cursors bersifat session-bound dan akan error/ditutup paksa oleh server.
# if _is_postgres:
#     DATABASES['default'].setdefault('OPTIONS', {})
#     DATABASES['default']['OPTIONS']['server_side_binding'] = True

# ============================================================
# SESSION
# Gunakan database session agar session konsisten di multi-process/multi-server.
# Pastikan jalankan: python manage.py createcachetable (jika pakai cache session)
# ============================================================
SESSION_ENGINE = 'django.contrib.sessions.backends.db'
SESSION_COOKIE_AGE = 86400 * 7  # 7 hari
SESSION_SAVE_EVERY_REQUEST = True  # Refresh expiry setiap request

# ============================================================
# STATIC & MEDIA FILES
# ============================================================
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# WhiteNoise: compress & cache static files di production
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# ============================================================
# INTERNATIONALIZATION
# ============================================================
LANGUAGE_CODE = 'id-id'
TIME_ZONE = 'Asia/Jakarta'
USE_I18N = True
USE_TZ = True

# ============================================================
# MISC
# ============================================================
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
