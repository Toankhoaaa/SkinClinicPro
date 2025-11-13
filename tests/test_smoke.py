import os
import django
from django.conf import settings
from django.core.management import call_command


def test_django_loads_settings():
    assert "appointments" in settings.INSTALLED_APPS


def test_system_checks_pass():
    # Use sqlite in CI/local by default unless overridden
    os.environ.setdefault("DB_ENGINE", "django.db.backends.sqlite3")
    django.setup()
    call_command("check")

