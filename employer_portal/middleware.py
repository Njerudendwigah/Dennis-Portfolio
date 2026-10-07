"""
Small security middleware for local development.

Some browser contexts can submit the staff login form with an opaque
``Origin: null`` even though the page is being served by Django on
localhost. That is a browser-context issue, not a missing CSRF token.

This middleware normalises that one development-only case to the actual
local Django origin before ``CsrfViewMiddleware`` runs.

Ordering
--------
This middleware must be placed:

* after ``django.middleware.common.CommonMiddleware``
  (so ``request.get_host()`` sees the parsed host), and
* before ``django.middleware.csrf.CsrfViewMiddleware``
  (so the normalised Origin is what CSRF sees).

``SecurityMiddleware`` runs earlier still, so ``request.is_secure()``
already reflects any trusted ``X-Forwarded-Proto`` header by the time
this class inspects the request.

Production safety
-----------------
* Active only when ``settings.DEBUG`` is ``True``.
* Only local hosts (``localhost``, ``127.0.0.1``, ``[::1]``) are eligible
  for normalisation.
* Only an exact ``Origin: null`` value is rewritten.
* Production requests are never touched.
"""

from __future__ import annotations

from django.conf import settings
from django.core.exceptions import DisallowedHost
from django.http import HttpRequest, HttpResponse


class LocalDevelopmentOriginMiddleware:
    """Normalise an opaque local ``Origin`` for Django's CSRF origin check."""

    LOCAL_HOSTS = frozenset(
        {
            "127.0.0.1",
            "localhost",
            "[::1]",
        }
    )

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        if settings.DEBUG:
            self._normalise_local_null_origin(request)

        return self.get_response(request)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _normalise_local_null_origin(self, request: HttpRequest) -> None:
        """
        Rewrite an opaque ``Origin: null`` to the concrete local origin.

        Exits quietly when the request is not eligible:

        * Origin is absent or is not exactly ``null``.
        * The ``Host`` header is rejected by ``ALLOWED_HOSTS``.
        * The host portion is not one of the accepted local hosts.
        """
        if request.META.get("HTTP_ORIGIN") != "null":
            return

        try:
            host_header = request.get_host()
        except DisallowedHost:
            # A host that is not in ALLOWED_HOSTS is never eligible for
            # normalisation — Django's host validation has already
            # rejected the request upstream.
            return

        if self._extract_host(host_header) not in self.LOCAL_HOSTS:
            return

        scheme = "https" if request.is_secure() else "http"
        request.META["HTTP_ORIGIN"] = f"{scheme}://{host_header}"

    @staticmethod
    def _extract_host(host_header: str) -> str:
        """
        Return the host portion of a ``Host`` header, preserving IPv6
        brackets and discarding any port.

        ``localhost:8000``  -> ``localhost``
        ``127.0.0.1:8000``  -> ``127.0.0.1``
        ``[::1]:8000``      -> ``[::1]``
        ``[::1]``           -> ``[::1]``
        """
        if host_header.startswith("["):
            end = host_header.find("]")
            if end != -1:
                return host_header[: end + 1]
        return host_header.split(":", 1)[0]