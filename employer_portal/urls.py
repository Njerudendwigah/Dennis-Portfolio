"""
URL configuration for the Dennis Ndwigah employer-access portal.

The route names in this module are part of the application's internal
contract. Templates, views, admin actions and tests depend on them, so
changes should preserve the existing names unless the entire integration
is updated together.

Mounting
--------
This module is designed to be included at ``/admin/employer-portal/`` so
that the staff-facing pages inherit the admin session and login flow::

    path(
        "admin/employer-portal/",
        include("employer_portal.urls", namespace="employer_portal"),
    ),

After that, the canonical staff dashboard URL is
``/admin/employer-portal/staff/dashboard/`` — which matches
``settings.LOGIN_REDIRECT_URL``.
"""

from __future__ import annotations

from django.conf import settings
from django.contrib.auth import views as auth_views
from django.urls import path

from . import forms, portfolio_api, views


app_name = "employer_portal"


urlpatterns = [
    # -----------------------------------------------------------------------
    # Staff authentication
    #
    # The portal ships its own themed login page (employer_portal/login.html)
    # so the two-factor prompt and the login branding stay consistent when
    # staff arrive via the public site. The admin login at /admin/login/
    # remains functional and shares the same session.
    # -----------------------------------------------------------------------
    path(
        "login/",
        auth_views.LoginView.as_view(
            template_name="employer_portal/login.html",
            authentication_form=forms.StaffAuthenticationForm,
            redirect_authenticated_user=True,
        ),
        name="login",
    ),
    path(
        "logout/",
        auth_views.LogoutView.as_view(
            next_page=settings.LOGOUT_REDIRECT_URL,
        ),
        name="logout",
    ),

    path(
    "api/portfolio/login/",
    portfolio_api.login,
    name="portfolio_api_login",
),
path(
    "api/portfolio/logout/",
    portfolio_api.logout,
    name="portfolio_api_logout",
),
path(
    "api/portfolio/data/",
    portfolio_api.data,
    name="portfolio_api_data",
),
path(
    "api/portfolio/data/<str:key>/",
     portfolio_api.section,
     name="portfolio_api_section",
    ),

    # -----------------------------------------------------------------------
    # Public employer access request flow
    # -----------------------------------------------------------------------
    path(
        "request-access/",
        views.request_access,
        name="request_access",
    ),
    path(
        "request-access/submitted/<uuid:request_id>/",
        views.request_submitted,
        name="request_submitted",
    ),
    path(
        "request-status/<uuid:request_id>/",
        views.request_status,
        name="request_status",
    ),

    # -----------------------------------------------------------------------
    # Secure employer portal (token-gated, no session required)
    # -----------------------------------------------------------------------
    path(
        "portal/<uuid:token>/",
        views.portal,
        name="portal",
    ),
    path(
        "portal/<uuid:token>/documents/<int:document_id>/view/",
        views.document_view,
        name="document_view",
    ),
    path(
        "portal/<uuid:token>/documents/<int:document_id>/stream/",
        views.document_stream,
        name="document_stream",
    ),
    path(
        "portal/<uuid:token>/documents/<int:document_id>/download/",
        views.document_download,
        name="document_download",
    ),
    path(
        "portal/<uuid:token>/referees/<int:referee_id>/",
        views.referee_view,
        name="referee_view",
    ),

    # -----------------------------------------------------------------------
    # Private staff review workflow
    #
    # The dashboard lives at staff/dashboard/ so that the containing URL
    # reads cleanly:  /admin/employer-portal/staff/dashboard/
    #
    # The remaining staff endpoints live under staff/requests/ so the URL
    # hierarchy mirrors the workflow (list -> detail -> action).
    # -----------------------------------------------------------------------
    path(
        "staff/dashboard/",
        views.staff_dashboard,
        name="staff_dashboard",
    ),
    path(
        "staff/requests/<uuid:request_id>/",
        views.staff_request_detail,
        name="staff_request_detail",
    ),
    path(
        "staff/requests/<uuid:request_id>/assign/",
        views.assign_request,
        name="assign_request",
    ),
    path(
        "staff/requests/<uuid:request_id>/approve/",
        views.approve_request,
        name="approve_request",
    ),
    path(
        "staff/requests/<uuid:request_id>/reject/",
        views.reject_request,
        name="reject_request",
    ),
    path(
        "staff/requests/<uuid:request_id>/revoke/",
        views.revoke_access,
        name="revoke_access",
    ),
]
