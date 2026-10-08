from __future__ import annotations

import logging
import sys
from pathlib import Path

from django.apps import AppConfig
from django.conf import settings
from django.core.checks import Error, Warning, register

logger = logging.getLogger(__name__)

__version__ = "1.0.0"


def _is_relative_to(child: Path, parent: Path) -> bool:
    """Return True when child is inside parent or is the same path."""
    try:
        child.relative_to(parent)
        return True
    except ValueError:
        return False


def _check_private_documents_root(app_configs, **kwargs):
    errors = []

    root = getattr(settings, "PRIVATE_DOCUMENTS_ROOT", None)

    if not root:
        return [
            Error(
                "PRIVATE_DOCUMENTS_ROOT is not configured.",
                hint=(
                    "Set PRIVATE_DOCUMENTS_ROOT to a writable directory "
                    "outside MEDIA_ROOT and STATIC_ROOT."
                ),
                id="employer_portal.E001",
            )
        ]

    root_path = Path(root).resolve()

    media_root_raw = getattr(settings, "MEDIA_ROOT", "") or ""
    static_root_raw = getattr(settings, "STATIC_ROOT", "") or ""

    media_root = Path(media_root_raw).resolve() if media_root_raw else None
    static_root = Path(static_root_raw).resolve() if static_root_raw else None

    if media_root and _is_relative_to(root_path, media_root):
        errors.append(
            Error(
                "PRIVATE_DOCUMENTS_ROOT is inside MEDIA_ROOT.",
                hint="Move PRIVATE_DOCUMENTS_ROOT outside MEDIA_ROOT.",
                id="employer_portal.E002",
            )
        )

    if static_root and _is_relative_to(root_path, static_root):
        errors.append(
            Error(
                "PRIVATE_DOCUMENTS_ROOT is inside STATIC_ROOT.",
                hint="Move PRIVATE_DOCUMENTS_ROOT outside STATIC_ROOT.",
                id="employer_portal.E003",
            )
        )

    if not root_path.exists():
        errors.append(
            Warning(
                f"PRIVATE_DOCUMENTS_ROOT does not exist yet: {root_path}",
                hint="It will be created automatically on startup.",
                id="employer_portal.W001",
            )
        )

    return errors


def _check_email_configuration(app_configs, **kwargs):
    if settings.DEBUG or "test" in sys.argv:
        return []

    errors = []

    mailers = getattr(settings, "MAILERS", {}) or {}
    default_mailer = mailers.get("default", {}) or {}

    backend = (
        default_mailer.get("BACKEND")
        or getattr(settings, "EMAIL_BACKEND", "")
        or ""
    )

    is_console_backend = backend.endswith(
        "django.core.mail.backends.console.EmailBackend"
    )

    if not is_console_backend:
        options = default_mailer.get("OPTIONS", {}) or {}
        email_host = (
            options.get("host")
            or getattr(settings, "EMAIL_HOST", "")
            or ""
        )

        if not str(email_host).strip():
            errors.append(
                Error(
                    "EMAIL_HOST is not set.",
                    hint=(
                        "Configure the SMTP host in MAILERS['default']['OPTIONS'] "
                        "or set EMAIL_HOST."
                    ),
                    id="employer_portal.E010",
                )
            )

    if not getattr(settings, "EMPLOYER_NOTIFICATION_EMAIL", "").strip():
        errors.append(
            Error(
                "EMPLOYER_NOTIFICATION_EMAIL is not set.",
                hint="Set EMPLOYER_NOTIFICATION_EMAIL.",
                id="employer_portal.E011",
            )
        )

    return errors


def _check_trust_x_forwarded_for(app_configs, **kwargs):
    errors = []

    trusts_xff = getattr(settings, "TRUST_X_FORWARDED_FOR", False)
    trusts_proto = getattr(settings, "USE_SECURE_PROXY_HEADER", False)

    if trusts_xff and not trusts_proto:
        errors.append(
            Warning(
                "TRUST_X_FORWARDED_FOR is enabled without "
                "USE_SECURE_PROXY_HEADER.",
                hint=(
                    "Enable DJANGO_USE_SECURE_PROXY_HEADER for a trusted "
                    "HTTPS proxy, or disable DJANGO_TRUST_X_FORWARDED_FOR."
                ),
                id="employer_portal.W010",
            )
        )

    return errors


class EmployerPortalConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "employer_portal"
    verbose_name = "Employer Access Portal"
    version = __version__

    _ready_has_run = False

    def ready(self) -> None:
        if type(self)._ready_has_run:
            return

        type(self)._ready_has_run = True

        from . import signals

        register(_check_private_documents_root)
        register(_check_email_configuration)
        register(_check_trust_x_forwarded_for)

        self._ensure_private_documents_root()

        logger.debug("employer_portal ready (v%s).", __version__)

    @staticmethod
    def _ensure_private_documents_root() -> None:
        root = getattr(settings, "PRIVATE_DOCUMENTS_ROOT", None)

        if not root:
            return

        try:
            Path(root).mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            logger.warning(
                "Could not create PRIVATE_DOCUMENTS_ROOT at %s: %s",
                root,
                exc,
            )
