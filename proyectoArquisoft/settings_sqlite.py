from .settings import *
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": str(BASE_DIR / "db.sqlite3"),
    }
}
# Evita cache/redis (opcional)
CACHES = {"default": {"BACKEND": "django.core.cache.backends.dummy.DummyCache"}}
