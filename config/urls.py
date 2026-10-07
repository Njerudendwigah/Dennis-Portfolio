"""
Root URL configuration for the Dennis Ndwigah portfolio project.

Three entry points:

    Public portfolio          /
    Staff portal              /employer/
    Django administration     /admin/

The employer portal owns its staff workflow under ``/employer/``.
A compatibility route keeps older/admin dashboard links working without
moving the real staff dashboard into Django's admin URL space.

Canonical staff dashboard URL:

    /employer/dashboard/

Compatibility URL:

    /admin/employer-portal/staff/dashboard/

The compatibility URL redirects to the canonical staff dashboard route.
"""

from __future__ import annotations

import mimetypes
from pathlib import Path

from django.conf import settings
from django.contrib import admin
from django.http import FileResponse, Http404, HttpRequest, HttpResponse
from django.urls import include, path
from django.views.generic import RedirectView


BASE_DIR = Path(settings.BASE_DIR)


# ---------------------------------------------------------------------------
# SAFE PUBLIC FILE HELPERS
# ---------------------------------------------------------------------------


def _safe_public_file(root: Path, relative_path: str) -> Path:
    """Resolve a public file while preventing path traversal."""
    root = root.resolve()
    candidate = (root / relative_path).resolve()

    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise Http404("Public asset not found.") from exc

    if not candidate.is_file():
        raise Http404("Public asset not found.")

    return candidate


def _file_response(
    file_path: Path,
    *,
    content_type: str | None = None,
    cache_control: str = "no-cache",
) -> FileResponse:
    """Return a controlled public file response."""
    guessed_type, _ = mimetypes.guess_type(file_path.name)

    response = FileResponse(
        file_path.open("rb"),
        content_type=(
            content_type
            or guessed_type
            or "application/octet-stream"
        ),
    )

    response["Cache-Control"] = cache_control
    response["X-Content-Type-Options"] = "nosniff"

    return response


# ---------------------------------------------------------------------------
# PUBLIC PORTFOLIO VIEWS
# ---------------------------------------------------------------------------


def portfolio_home(request: HttpRequest) -> HttpResponse:
    """Serve index.html only at the public root URL."""
    index_path = _safe_public_file(BASE_DIR, "index.html")

    return _file_response(
        index_path,
        content_type="text/html; charset=utf-8",
        cache_control="no-cache",
    )


def portfolio_stylesheet(request: HttpRequest) -> HttpResponse:
    """Serve the public stylesheet."""
    stylesheet = _safe_public_file(BASE_DIR, "styles.css")

    return _file_response(
        stylesheet,
        content_type="text/css; charset=utf-8",
        cache_control="no-cache",
    )


def portfolio_css_asset(request: HttpRequest, path: str) -> HttpResponse:
    """Serve public CSS assets from the project's css directory."""
    asset = _safe_public_file(BASE_DIR / "css", path)

    return _file_response(
        asset,
        content_type="text/css; charset=utf-8",
        cache_control="public, max-age=86400",
    )


def portfolio_js_asset(request: HttpRequest, path: str) -> HttpResponse:
    """Serve public JavaScript assets from the project's js directory."""
    asset = _safe_public_file(BASE_DIR / "js", path)

    return _file_response(
        asset,
        content_type="text/javascript; charset=utf-8",
        cache_control="public, max-age=86400",
    )


def portfolio_image_asset(request: HttpRequest, path: str) -> HttpResponse:
    """Serve public images from the project's images directory."""
    asset = _safe_public_file(BASE_DIR / "images", path)

    return _file_response(
        asset,
        cache_control="public, max-age=86400",
    )


def portfolio_favicon(request: HttpRequest) -> HttpResponse:
    """Serve the public favicon."""
    favicon = _safe_public_file(
        BASE_DIR / "images",
        "favicon.png",
    )

    return _file_response(
        favicon,
        content_type="image/png",
        cache_control="public, max-age=86400",
    )


def portfolio_robots(request: HttpRequest) -> HttpResponse:
    """Serve robots.txt when present."""
    robots = _safe_public_file(BASE_DIR, "robots.txt")

    return _file_response(
        robots,
        content_type="text/plain; charset=utf-8",
        cache_control="public, max-age=3600",
    )


def portfolio_sitemap(request: HttpRequest) -> HttpResponse:
    """Serve sitemap.xml when present."""
    sitemap = _safe_public_file(BASE_DIR, "sitemap.xml")

    return _file_response(
        sitemap,
        content_type="application/xml; charset=utf-8",
        cache_control="public, max-age=3600",
    )


# ---------------------------------------------------------------------------
# URL CONFIGURATION
# ---------------------------------------------------------------------------

urlpatterns = [
    # The compatibility route must appear BEFORE admin.site.urls because
    # Django admin owns the /admin/ namespace and includes a catch-all route.

    # -----------------------------------------------------------------------
    # Staff dashboard compatibility route
    # -----------------------------------------------------------------------
    path(
        "admin/employer-portal/staff/dashboard/",
        RedirectView.as_view(
            pattern_name="employer_portal:staff_dashboard",
            permanent=False,
        ),
        name="admin_employer_staff_dashboard",
    ),

    # -----------------------------------------------------------------------
    # Django administration
    # -----------------------------------------------------------------------
    path(
        "admin/",
        admin.site.urls,
    ),

    # -----------------------------------------------------------------------
    # Staff portal
    # -----------------------------------------------------------------------
    path(
        "employer/",
        include("employer_portal.urls"),
    ),

    # -----------------------------------------------------------------------
    # Public portfolio root
    # -----------------------------------------------------------------------
    path(
        "",
        portfolio_home,
        name="portfolio_home",
    ),

    # -----------------------------------------------------------------------
    # Public portfolio files
    # -----------------------------------------------------------------------
    path(
        "styles.css",
        portfolio_stylesheet,
        name="portfolio_stylesheet",
    ),
    path(
        "favicon.png",
        portfolio_favicon,
        name="portfolio_favicon",
    ),
    path(
        "robots.txt",
        portfolio_robots,
        name="portfolio_robots",
    ),
    path(
        "sitemap.xml",
        portfolio_sitemap,
        name="portfolio_sitemap",
    ),
    path(
        "css/<path:path>",
        portfolio_css_asset,
        name="portfolio_css_asset",
    ),
    path(
        "js/<path:path>",
        portfolio_js_asset,
        name="portfolio_js_asset",
    ),
    path(
        "images/<path:path>",
        portfolio_image_asset,
        name="portfolio_image_asset",
    ),
]


# ---------------------------------------------------------------------------
# DEVELOPMENT MEDIA SERVING
#
# Only in DEBUG, and only for non-private media. Files under
# settings.PRIVATE_DOCUMENTS_ROOT are intentionally never served here.
# ---------------------------------------------------------------------------

if settings.DEBUG:
    from django.conf.urls.static import static

    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT,
    )
