"""
Dashboard data for the Unfold admin home page.
...
"""

from __future__ import annotations

import json
from datetime import datetime, time, timedelta
from urllib.parse import urlencode

from django.conf import settings
from django.db import models
from django.db.models import Count
from django.db.models.functions import TruncDate
from django.urls import reverse
from django.utils import timezone

from .models import (
    AccessGrant,
    AccessLog,
    AccessRequest,
    Document,
    Employer,
)


VIEW_EVENTS = (
    AccessLog.EventType.DOCUMENT_VIEWED,
    AccessLog.EventType.DOCUMENT_DOWNLOADED,
    AccessLog.EventType.REFEREE_VIEWED,
    AccessLog.EventType.PORTAL_VIEWED,
)


STATUS_CLASSES = {
    "pending": "bg-orange-100 text-orange-700 dark:bg-orange-500/20 dark:text-orange-400",
    "approved": "bg-green-100 text-green-700 dark:bg-green-500/20 dark:text-green-400",
    "rejected": "bg-red-100 text-red-700 dark:bg-red-500/20 dark:text-red-400",
    "expired": "bg-blue-100 text-blue-700 dark:bg-blue-500/20 dark:text-blue-400",
    "revoked": "bg-red-100 text-red-700 dark:bg-red-500/20 dark:text-red-400",
}


# ---------------------------------------------------------------------------
# Date helpers
# ---------------------------------------------------------------------------


def _start_of_day(date_value):
    """Return a timezone-aware datetime at the start of the given date."""
    naive = datetime.combine(date_value, time.min)
    return timezone.make_aware(naive, timezone.get_current_timezone())


# ---------------------------------------------------------------------------
# Sidebar badge
# ---------------------------------------------------------------------------


def pending_requests_badge(request):
    """Return the pending-request count, hiding the badge when the count is zero."""
    count = AccessRequest.objects.pending().count()
    return count or None


# ---------------------------------------------------------------------------
# Admin URL helpers
# ---------------------------------------------------------------------------


def _admin_url(name: str, **query) -> str:
    """Build an admin changelist URL with safely encoded query parameters."""
    url = reverse(f"admin:employer_portal_{name}_changelist")
    if query:
        url = f"{url}?{urlencode(query, doseq=True)}"
    return url


# ---------------------------------------------------------------------------
# Chart data
# ---------------------------------------------------------------------------


def _activity_chart(days: int = 7) -> str:
    """Return JSON for the employer activity chart."""
    if days < 1:
        raise ValueError("days must be at least 1")

    today = timezone.localdate()
    start = today - timedelta(days=days - 1)

    # Use a range query rather than `created_at__date__gte` so the
    # timestamp index on AccessLog.created_at is usable.
    start_dt = _start_of_day(start)

    rows = (
        AccessLog.objects.filter(
            event_type__in=VIEW_EVENTS,
            created_at__gte=start_dt,
        )
        .annotate(day=TruncDate("created_at"))
        .values("day")
        .annotate(total=Count("id"))
        .order_by("day")
    )

    counts = {row["day"]: row["total"] for row in rows}

    labels = []
    values = []
    for i in range(days):
        day = start + timedelta(days=i)
        labels.append(day.strftime("%a %d"))
        values.append(counts.get(day, 0))

    return json.dumps(
        {
            "labels": labels,
            "datasets": [
                {
                    "label": "Employer views and downloads",
                    "data": values,
                    "backgroundColor": "oklch(60% .118 184.704)",
                    "borderRadius": 6,
                    "barPercentage": 0.6,
                    "maxBarThickness": 56,
                }
            ],
        }
    )


# ---------------------------------------------------------------------------
# Dashboard callback
# ---------------------------------------------------------------------------


def dashboard_callback(request, context):
    """Populate the Unfold admin home page with employer-portal data."""
    now = timezone.now()
    week_ago = now - timedelta(days=7)
    three_days_from_now = now + timedelta(days=3)

    # ---- Access request KPIs ----------------------------------------
    pending_count = AccessRequest.objects.pending().count()

    # ---- Access grant KPIs ------------------------------------------
    active_grants_qs = AccessGrant.objects.filter(
        is_active=True,
        revoked_at__isnull=True,
        starts_at__lte=now,
        expires_at__gt=now,
        access_request__status=AccessRequest.Status.APPROVED,
    )
    active_grant_count = active_grants_qs.count()

    expiring_soon_qs = (
        active_grants_qs
        .filter(expires_at__lte=three_days_from_now)
        .select_related("access_request")
        .order_by("expires_at")
    )
    expiring_soon_count = expiring_soon_qs.count()

    # ---- Employer KPIs ----------------------------------------------
    employer_stats = Employer.objects.aggregate(
        verified=Count("pk", filter=models.Q(is_verified=True)),
        total=Count("pk"),
    )
    # Need Q import for the above. Alternatively:

    verified_employers = Employer.objects.filter(is_verified=True).count()
    total_employers = Employer.objects.count()

    # ---- Documents ---------------------------------------------------
    documents_count = Document.objects.active().count()

    # ---- Views this week ---------------------------------------------
    views_this_week = AccessLog.objects.filter(
        event_type__in=VIEW_EVENTS,
        created_at__gte=week_ago,
    ).count()

    # ---- Recent requests ---------------------------------------------
    recent_requests = [
        {
            "name": ar.requester_name or "—",
            "company": ar.requester_company or "—",
            "status": ar.get_status_display(),
            "status_class": STATUS_CLASSES.get(ar.status, ""),
            "created_at": ar.created_at,
            "url": reverse(
                "admin:employer_portal_accessrequest_change",
                args=[ar.pk],
            ),
        }
        for ar in (
            AccessRequest.objects
            .select_related("employer")
            .order_by("-created_at")[:6]
        )
    ]

    # ---- Recent activity ---------------------------------------------
    recent_activity = [
        {
            "event": log.get_event_type_display(),
            "who": log.actor_label,
            "ip": log.ip_address or "",
            "created_at": log.created_at,
        }
        for log in (
            AccessLog.objects
            .select_related("employer", "access_request")
            .order_by("-created_at")[:6]
        )
    ]

    # ---- Expiring soon list ------------------------------------------
    expiring_soon_list = [
        {
            "name": g.access_request.requester_name or "—",
            "company": g.access_request.requester_company or "—",
            "expires_at": g.expires_at,
        }
        for g in expiring_soon_qs[:5]
    ]

    context.update(
        {
            "kpis": [
                {
                    "title": "Pending requests",
                    "value": pending_count,
                    "icon": "pending_actions",
                    "hint": "Waiting for your review",
                    "href": _admin_url(
                        "accessrequest",
                        status__exact=AccessRequest.Status.PENDING,
                    ),
                },
                {
                    "title": "Active grants",
                    "value": active_grant_count,
                    "icon": "key",
                    "hint": f"{expiring_soon_count} expiring in 3 days",
                    "href": _admin_url("accessgrant", is_active__exact=1),
                },
                {
                    "title": "Views this week",
                    "value": views_this_week,
                    "icon": "visibility",
                    "hint": "Portal, document and referee views",
                    "href": _admin_url("accesslog"),
                },
                {
                    "title": "Verified employers",
                    "value": verified_employers,
                    "icon": "verified",
                    "hint": f"{total_employers} employers in total",
                    "href": _admin_url("employer", is_verified__exact=1),
                },
            ],
            "chart_data": _activity_chart(),
            "recent_requests": recent_requests,
            "recent_activity": recent_activity,
            "expiring_soon": expiring_soon_list,
            "documents_count": documents_count,
        }
    )

    return context


# ---------------------------------------------------------------------------
# Environment label
# ---------------------------------------------------------------------------


def environment_callback(request):
    """Show the current Development / Production label in the admin header."""
    if settings.DEBUG:
        return ["Development", "info"]
    return ["Production", "success"]