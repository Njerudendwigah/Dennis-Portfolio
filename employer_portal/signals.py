"""
Signal receivers for the employer access portal.

Registers two authentication-event audit hooks:

* ``user_logged_in``  -> ``AccessLog.EventType.LOGIN``
* ``user_logged_out`` -> ``AccessLog.EventType.LOGOUT``

Both are restricted to staff users. Non-staff logins (should the portal
ever add employer-side accounts) are ignored so the audit trail stays
focused on staff actions.

Design notes
------------
* Every write goes through ``AccessLog.log_from_request`` so client IP
  and user-agent are captured consistently with the admin and public
  views.
* Writes are wrapped in a broad ``try/except``. An audit failure must
  never break a user's ability to log in or out — the login flow is
  more important than the log entry.
* ``request`` may be ``None`` in some auth flows (programmatic
  ``login()``, test suites, ``force_login``). The helper falls back to a
  plain ``AccessLog.objects.create`` in that case.
* ``dispatch_uid`` prevents duplicate registration if the module is ever
  re-imported, at the cost of an anonymous module-level string.
"""

from __future__ import annotations

import logging

from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.dispatch import receiver

from .models import AccessLog

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# INTERNAL HELPERS
# ---------------------------------------------------------------------------


def _write_audit(request, event_type: str, *, user=None) -> None:
    """
    Best-effort audit write.

    Swallows every exception so a broken audit path (missing table
    during a partial migration, locked database, replica lag) cannot
    prevent a staff user from authenticating.
    """
    metadata: dict = {"source": "signal"}
    if user is not None:
        metadata["username"] = user.get_username()
        if user.pk is not None:
            metadata["user_id"] = user.pk

    try:
        if request is None:
            # ``force_login``, test helpers, or a programmatic session
            # without an HTTP request. No IP/UA to capture.
            AccessLog.objects.create(
                event_type=event_type,
                resource_type="staff_session",
                resource_identifier=str(getattr(user, "pk", "") or ""),
                metadata=metadata,
            )
        else:
            AccessLog.log_from_request(
                request,
                event_type,
                resource_type="staff_session",
                resource_identifier=str(getattr(user, "pk", "") or ""),
                metadata=metadata,
            )
    except Exception:
        # Never propagate — logging failure must not block auth.
        logger.exception(
            "Failed to write %s audit entry for user %r.",
            event_type,
            getattr(user, "get_username", lambda: None)(),
        )


# ---------------------------------------------------------------------------
# STAFF LOGIN
# ---------------------------------------------------------------------------


@receiver(
    user_logged_in,
    dispatch_uid="employer_portal.log_staff_login",
)
def log_staff_login(sender, request, user, **kwargs) -> None:
    """Record a ``LOGIN`` audit event for staff users only."""
    if user is None or not getattr(user, "is_staff", False):
        return
    _write_audit(request, AccessLog.EventType.LOGIN, user=user)


# ---------------------------------------------------------------------------
# STAFF LOGOUT
# ---------------------------------------------------------------------------


@receiver(
    user_logged_out,
    dispatch_uid="employer_portal.log_staff_logout",
)
def log_staff_logout(sender, request, user, **kwargs) -> None:
    """
    Record a ``LOGOUT`` audit event for staff users only.

    Django 4.1+ may pass ``user=None`` when the session is invalidated
    without an explicit user context (session expiry, cookie clearing).
    That case is skipped rather than logged as "System".
    """
    if user is None or not getattr(user, "is_staff", False):
        return
    _write_audit(request, AccessLog.EventType.LOGOUT, user=user)


# ---------------------------------------------------------------------------
# OPTIONAL — FAILED LOGIN ATTEMPTS
# ---------------------------------------------------------------------------
#
# Uncomment to audit failed staff authentication attempts. Useful for
# spotting brute-force activity, but noisy: it fires for every wrong
# password, including typos from legitimate staff.
#
# from django.contrib.auth.signals import user_login_failed
#
#
# @receiver(
#     user_login_failed,
#     dispatch_uid="employer_portal.log_failed_login",
# )
# def log_failed_login(sender, credentials, request, **kwargs) -> None:
#     username = (credentials or {}).get("username", "")
#     # Best-effort: only log usernames that already belong to a staff
#     # account, so probing for non-existent users produces no audit noise.
#     from django.contrib.auth import get_user_model
#     User = get_user_model()
#     if not User.objects.filter(username=username, is_staff=True).exists():
#         return
#     try:
#         if request is not None:
#             AccessLog.log_from_request(
#                 request,
#                 AccessLog.EventType.LOGIN,
#                 resource_type="staff_session",
#                 resource_identifier=username,
#                 metadata={"outcome": "failed", "username": username},
#             )
#     except Exception:
#         logger.exception("Failed to write failed-login audit entry.")