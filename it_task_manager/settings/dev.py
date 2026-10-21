from decouple import Csv, config

from .base import *  # noqa: F401,F403

DEBUG = config("DEBUG", default=True, cast=bool)

ALLOWED_HOSTS = config("ALLOWED_HOSTS", default="127.0.0.1,localhost", cast=Csv())

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
