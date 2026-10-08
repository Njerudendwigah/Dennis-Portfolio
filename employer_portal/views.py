"""

Views for the employer access portal.

The staff dashboard renders ``employer_portal/staff_dashboard.html`` — a

self-contained, tabbed triage workspace with its own rail and theme. It

does not extend ``admin/base.html`` and does not depend on

``admin_site.each_context()``.

Domain mutations (approve / reject / revoke / expire) are performed via

methods on ``AccessRequest`` so the admin and public views share one

code path. Audit logging is centralised in ``log_event()``, which

delegates to ``AccessLog.log_from_request()`` to capture client IP and

user-agent consistently.

"""

from __future__ import annotations

from datetime import timedelta

from functools import wraps

from mimetypes import guess_type

from pathlib import Path

from django.conf import settings

from django.contrib import messages

from django.contrib.auth.views import redirect_to_login

from django.core.exceptions import PermissionDenied

from django.core.mail import send_mail

from django.db import transaction

from django.http import (

    FileResponse,

    Http404,

    HttpRequest,

    HttpResponse,

)

from django.shortcuts import get_object_or_404, redirect, render

from django.urls import reverse

from django.utils import timezone
from django.utils.html import escape

from django.views.decorators.http import (

    require_GET,

    require_POST,

    require_http_methods,

)

from .forms import AccessRequestForm

from .models import (

    AccessGrant,

    AccessLog,

    AccessRequest,

    Document,

    DocumentAccessRequest,

    Employer,

    Referee,

    RefereeAccessRequest,

)

DEFAULT_ACCESS_DURATION_DAYS = 7

# ---------------------------------------------------------------------------

# ACCESS CONTROL

# ---------------------------------------------------------------------------

def staff_required(view_func):

    """Require an authenticated Django staff account."""

    @wraps(view_func)

    def wrapped_view(request, *args, **kwargs):

        if not request.user.is_authenticated:

            return redirect_to_login(

                request.get_full_path(),

                settings.LOGIN_URL,

            )

        if not request.user.is_active or not request.user.is_staff:

            raise PermissionDenied("Active staff access is required.")

        return view_func(request, *args, **kwargs)

    return wrapped_view

# ---------------------------------------------------------------------------

# AUDIT LOGGING

# ---------------------------------------------------------------------------

def log_event(

    event_type: str,

    request: HttpRequest | None = None,

    *,

    access_request: AccessRequest | None = None,

    employer: Employer | None = None,

    resource_type: str = "",

    resource_identifier: str | int | None = None,

    metadata: dict | None = None,

) -> AccessLog:

    """

    Create an immutable audit record.

    Delegates to ``AccessLog.log_from_request`` when a request is

    available (captures IP + UA), otherwise falls back to a plain create

    for management-command / signal callers.

    """

    identifier = str(resource_identifier) if resource_identifier is not None else ""

    meta = metadata or {}

    if request is None:

        return AccessLog.objects.create(

            event_type=event_type,

            access_request=access_request,

            employer=employer,

            resource_type=resource_type,

            resource_identifier=identifier,

            metadata=meta,

        )

    return AccessLog.log_from_request(

        request,

        event_type,

        access_request=access_request,

        employer=employer,

        resource_type=resource_type,

        resource_identifier=identifier,

        metadata=meta,

    )

# ---------------------------------------------------------------------------

# GRANT HELPERS

# ---------------------------------------------------------------------------

def get_valid_grant(token) -> AccessGrant | None:

    """

    Return a currently valid grant for the given token, or ``None``.

    Automatically marks the grant as expired (and its request as

    ``EXPIRED``) when the window has passed — self-healing on each call.

    """

    now = timezone.now()

    grant = (

        AccessGrant.objects

        .select_related("access_request", "access_request__employer")

        .filter(

            token=token,

            is_active=True,

            starts_at__lte=now,

            access_request__status=AccessRequest.Status.APPROVED,

        )

        .first()

    )

    if grant is None:

        return None

    if grant.expires_at <= now:

        grant.access_request.mark_expired(now=now)

        return None

    return grant

# ---------------------------------------------------------------------------

# RESOURCE LOOKUPS

# ---------------------------------------------------------------------------

def _approved_documents(access_request: AccessRequest):

    return list(

        Document.objects

        .filter(

            access_request_items__access_request=access_request,

            access_request_items__approved=True,

            is_active=True,

        )

        .distinct()

        .order_by("document_type", "title")

    )

def _approved_referees(access_request: AccessRequest):

    return list(

        Referee.objects

        .filter(

            access_request_items__access_request=access_request,

            access_request_items__approved=True,

            is_active=True,

        )

        .distinct()

        .order_by("name")

    )

def _requested_documents_for_review(access_request: AccessRequest):

    return list(

        Document.objects

        .filter(

            access_request_items__access_request=access_request,

            is_active=True,

        )

        .distinct()

        .order_by("document_type", "title")

    )

def _requested_referees_for_review(access_request: AccessRequest):

    return list(

        Referee.objects

        .filter(

            access_request_items__access_request=access_request,

            is_active=True,

        )

        .distinct()

        .order_by("name")

    )

def _resource_availability(form: AccessRequestForm):

    """Return whether active documents or referees are selectable."""

    document_field = (

        form.fields.get("requested_documents") or form.fields.get("documents")

    )

    referee_field = (

        form.fields.get("requested_referees") or form.fields.get("referees")

    )

    has_documents = bool(

        document_field is not None

        and hasattr(document_field, "queryset")

        and document_field.queryset.exists()

    )

    has_referees = bool(

        referee_field is not None

        and hasattr(referee_field, "queryset")

        and referee_field.queryset.exists()

    )

    return has_documents, has_referees

# ---------------------------------------------------------------------------

# EMAIL HELPERS

# ---------------------------------------------------------------------------

def _notify_staff_of_new_request(

    request: HttpRequest,

    access_request: AccessRequest,

) -> tuple[bool, str]:

    """Send the staff notification email. Returns (sent, error)."""

    recipient = getattr(settings, "EMPLOYER_NOTIFICATION_EMAIL", "")

    if not recipient:

        return False, ""

    try:

        review_url = request.build_absolute_uri(

            reverse(

                "employer_portal:staff_request_detail",

                kwargs={"request_id": access_request.request_id},

            )

        )

        subject = (

            "New employer access request — "

            f"{access_request.requester_company or 'Unspecified company'}"

        )

        message = "\n".join(

            [

                "A new employer access request has been submitted.",

                "",

                f"Requester: {access_request.requester_name}",

                f"Email: {access_request.requester_email}",

                f"Company: {access_request.requester_company or 'Not provided'}",

                f"Job title: {access_request.requester_job_title or 'Not provided'}",

                f"Phone: {access_request.requester_phone or 'Not provided'}",

                "",

                "Reason for access:",

                access_request.reason or "Not provided",

                "",

                f"Request reference: {access_request.request_id}",

                f"Review request: {review_url}",

            ]

        )

        send_mail(

            subject=subject,

            message=message,

            from_email=getattr(settings, "DEFAULT_FROM_EMAIL", None),

            recipient_list=[recipient],

            fail_silently=False,

        )

        return True, ""

    except Exception as exc:

        return False, str(exc)[:500]

def _notify_employer_of_approval(request, access_request, grant):
    recipient = access_request.requester_email

    portal_url = request.build_absolute_uri(
        reverse(
            "employer_portal:portal",
            kwargs={"token": grant.token},
        )
    )

    subject = "Employer access request approved"

    message = (
        f"Hello {access_request.requester_name},\n\n"
        "Your request to access my professional portfolio has been approved.\n\n"
        "Your secure access link is:\n"
        f"{portal_url}\n\n"
        "This link provides access only to the information approved for your request "
        "and will expire according to the access period granted.\n\n"
        "Regards,\n"
        "Dennis Ndwigah"
    )

    html_message = f"""
    <html>
      <body>
        <p>Hello {escape(access_request.requester_name)},</p>

        <p>
          Your request to access my professional portfolio has been approved.
        </p>

        <p>
          Click the button below to access the approved information:
        </p>

        <p>
          <a href="{escape(portal_url)}"
             style="display:inline-block;
                    padding:12px 20px;
                    background:#111827;
                    color:#ffffff;
                    text-decoration:none;
                    border-radius:6px;">
            Open Secure Portfolio
          </a>
        </p>

        <p>
          This secure link provides access only to the information approved
          for your request and will expire according to the access period granted.
        </p>

        <p>
          Regards,<br>
          Dennis Ndwigah
        </p>
      </body>
    </html>
    """

    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[recipient],
            html_message=html_message,
            fail_silently=False,
        )
        return True, ""
    except Exception as exc:
        return False, str(exc)[:500]
@require_http_methods(["GET", "POST"])

def request_access(request: HttpRequest) -> HttpResponse:

    """Display and process the public employer access-request form."""

    if request.method == "POST":

        form = AccessRequestForm(request.POST)

        if not form.is_valid():

            has_documents, has_referees = _resource_availability(form)

            return render(

                request,

                "employer_portal/request_access.html",

                {

                    "form": form,

                    "has_documents": has_documents,

                    "has_referees": has_referees,

                    "has_resources": has_documents or has_referees,

                },

                status=400,

            )

        access_request = form.save(commit=True)

        access_request.ip_address = request.META.get("REMOTE_ADDR", "")

        access_request.user_agent = (request.META.get("HTTP_USER_AGENT") or "")[:512]

        access_request.save(

            update_fields=["ip_address", "user_agent", "updated_at"]

        )

        notification_sent, notification_error = _notify_staff_of_new_request(

            request, access_request

        )

        log_event(

            AccessLog.EventType.REQUEST_SUBMITTED,

            request,

            access_request=access_request,

            employer=access_request.employer,

            resource_type="access_request",

            resource_identifier=access_request.request_id,

            metadata={

                "requester_name": access_request.requester_name,

                "requester_email": access_request.requester_email,

                "requester_company": access_request.requester_company,

                "staff_notification_sent": notification_sent,

                **(

                    {"staff_notification_error": notification_error}

                    if notification_error

                    else {}

                ),

            },

        )

        return redirect(

            "employer_portal:request_submitted",

            request_id=access_request.request_id,

        )

    form = AccessRequestForm()

    has_documents, has_referees = _resource_availability(form)

    return render(

        request,

        "employer_portal/request_access.html",

        {

            "form": form,

            "has_documents": has_documents,

            "has_referees": has_referees,

            "has_resources": has_documents or has_referees,

        },

    )

@require_GET

def request_submitted(request: HttpRequest, request_id) -> HttpResponse:

    """Show the confirmation page for a submitted request."""

    access_request = get_object_or_404(

        AccessRequest.objects.select_related("employer"),

        request_id=request_id,

    )

    response = render(

        request,

        "employer_portal/request_submitted.html",

        {

            "access_request": access_request,

            "request_id": access_request.request_id,

        },

    )

    response["Cache-Control"] = "private, no-store, max-age=0"

    response["Pragma"] = "no-cache"

    return response

@require_GET

def request_status(request: HttpRequest, request_id) -> HttpResponse:

    """Show request status without treating the UUID as document authority."""

    access_request = get_object_or_404(

        AccessRequest.objects.select_related("employer", "reviewed_by", "grant"),

        request_id=request_id,

    )

    grant = getattr(access_request, "grant", None)

    # Self-heal if the grant window has passed.

    if (

        grant is not None

        and grant.is_active

        and grant.expires_at <= timezone.now()

    ):

        access_request.mark_expired()

        access_request.refresh_from_db(fields=["status", "updated_at"])

        grant.refresh_from_db(fields=["is_active", "revoked_at"])

    response = render(

        request,

        "employer_portal/request_status.html",

        {

            "access_request": access_request,

            "grant": grant,

        },

    )

    response["Cache-Control"] = "private, no-store, max-age=0"

    response["Pragma"] = "no-cache"

    return response

# ---------------------------------------------------------------------------

# EMPLOYER PORTAL

# ---------------------------------------------------------------------------

@require_GET

def portal(request: HttpRequest, token) -> HttpResponse:

    """Render the secure employer portal for a valid grant token."""

    grant = get_valid_grant(token)

    if grant is None:

        raise Http404("This employer access link is invalid or has expired.")

    access_request = grant.access_request

    documents = _approved_documents(access_request)

    referees = _approved_referees(access_request)

    log_event(

        AccessLog.EventType.PORTAL_VIEWED,

        request,

        access_request=access_request,

        employer=access_request.employer,

        resource_type="portal",

        resource_identifier=grant.token,

        metadata={

            "documents_available": len(documents),

            "referees_available": len(referees),

        },

    )

    response = render(

        request,

        "employer_portal/portal.html",

        {

            "grant": grant,

            "access_request": access_request,

            "documents": documents,

            "referees": referees,

        },

    )

    response["Cache-Control"] = "private, no-store, max-age=0"

    response["Pragma"] = "no-cache"

    return response

def _get_grant_document(grant: AccessGrant, document_id: int) -> Document:

    return get_object_or_404(

        DocumentAccessRequest.objects.select_related("document"),

        access_request=grant.access_request,

        document_id=document_id,

        approved=True,

        document__is_active=True,

    ).document

def _get_grant_referee(grant: AccessGrant, referee_id: int) -> Referee:

    return get_object_or_404(

        RefereeAccessRequest.objects.select_related("referee"),

        access_request=grant.access_request,

        referee_id=referee_id,

        approved=True,

        referee__is_active=True,

    ).referee

def _open_private_document(document: Document):

    if not document.file:

        raise Http404("The requested document is unavailable.")

    storage = document.file.storage

    if not storage.exists(document.file.name):

        raise Http404("The requested document is unavailable.")

    try:

        return storage.open(document.file.name, "rb")

    except (FileNotFoundError, OSError):

        raise Http404("The requested document is unavailable.")

def _mark_document_viewed(access_request: AccessRequest, document: Document) -> None:

    item = DocumentAccessRequest.objects.filter(

        access_request=access_request,

        document=document,

    ).first()

    if item is not None and item.viewed_at is None:

        item.mark_viewed()

def _mark_referee_viewed(access_request: AccessRequest, referee: Referee) -> None:

    item = RefereeAccessRequest.objects.filter(

        access_request=access_request,

        referee=referee,

    ).first()

    if item is not None and item.viewed_at is None:

        item.mark_viewed()

@require_GET

def document_view(

    request: HttpRequest,

    token,

    document_id: int,

) -> HttpResponse:

    """

    Render the secure document preview page.

    The page does not expose the private file path. The browser loads the

    protected file through ``document_stream`` using the same grant checks.

    """

    grant = get_valid_grant(token)

    if grant is None:

        raise Http404("This employer access link is invalid or has expired.")

    document = _get_grant_document(grant, document_id)

    _mark_document_viewed(grant.access_request, document)

    log_event(

        AccessLog.EventType.DOCUMENT_VIEWED,

        request,

        access_request=grant.access_request,

        employer=grant.access_request.employer,

        resource_type="document",

        resource_identifier=document.id,

        metadata={

            "document_title": document.title,

            "document_type": document.document_type,

            "grant_token": str(grant.token),

        },

    )

    return render(

        request,

        "employer_portal/document_preview.html",

        {

            "grant": grant,

            "access_request": grant.access_request,

            "document": document,

            "stream_url": reverse(

                "employer_portal:document_stream",

                kwargs={

                    "token": grant.token,

                    "document_id": document.id,

                },

            ),

            "download_url": reverse(

                "employer_portal:document_download",

                kwargs={

                    "token": grant.token,

                    "document_id": document.id,

                },

            ),

            "portal_url": reverse(

                "employer_portal:portal",

                kwargs={"token": grant.token},

            ),

        },

    )

@require_GET

def document_stream(

    request: HttpRequest,

    token,

    document_id: int,

) -> FileResponse:

    """

    Stream one approved private document to the preview page.

    The grant and document permissions are re-checked for every request so

    the preview endpoint cannot be used after access is revoked or expires.

    """

    grant = get_valid_grant(token)

    if grant is None:

        raise Http404("This employer access link is invalid or has expired.")

    document = _get_grant_document(grant, document_id)

    file_handle = _open_private_document(document)

    filename = Path(document.file.name).name

    guessed_type, _ = guess_type(filename)

    content_type = guessed_type or "application/octet-stream"

    response = FileResponse(

        file_handle,

        content_type=content_type,

    )

    response["Content-Disposition"] = f'inline; filename="{filename}"'

    response["X-Content-Type-Options"] = "nosniff"

    response["Cache-Control"] = "private, no-store, no-cache, must-revalidate"

    response["Pragma"] = "no-cache"

    response["Expires"] = "0"

    response["Referrer-Policy"] = "no-referrer"

    return response

@require_GET

def document_download(

    request: HttpRequest,

    token,

    document_id: int,

) -> FileResponse:

    """Download an explicitly approved private document."""

    grant = get_valid_grant(token)

    if grant is None:

        raise Http404("This employer access link is invalid or has expired.")

    document = _get_grant_document(grant, document_id)

    file_handle = _open_private_document(document)

    filename = Path(document.file.name).name

    _mark_document_viewed(grant.access_request, document)

    log_event(

        AccessLog.EventType.DOCUMENT_DOWNLOADED,

        request,

        access_request=grant.access_request,

        employer=grant.access_request.employer,

        resource_type="document",

        resource_identifier=document.id,

        metadata={

            "document_title": document.title,

            "document_type": document.document_type,

            "grant_token": str(grant.token),

        },

    )

    response = FileResponse(

        file_handle,

        content_type="application/octet-stream",

        as_attachment=True,

        filename=filename,

    )

    response["X-Content-Type-Options"] = "nosniff"

    response["Cache-Control"] = "private, no-store, no-cache, must-revalidate"

    response["Pragma"] = "no-cache"

    response["Expires"] = "0"

    return response

@require_GET

def referee_view(

    request: HttpRequest,

    token,

    referee_id: int,

) -> HttpResponse:

    """Render a referee record only when explicitly approved."""

    grant = get_valid_grant(token)

    if grant is None:

        raise Http404("This employer access link is invalid or has expired.")

    referee = _get_grant_referee(grant, referee_id)

    _mark_referee_viewed(grant.access_request, referee)

    log_event(

        AccessLog.EventType.REFEREE_VIEWED,

        request,

        access_request=grant.access_request,

        employer=grant.access_request.employer,

        resource_type="referee",

        resource_identifier=referee.id,

        metadata={

            "referee_name": referee.name,

            "organisation": referee.organisation,

            "grant_token": str(grant.token),

        },

    )

    response = render(

        request,

        "employer_portal/referee.html",

        {

            "grant": grant,

            "access_request": grant.access_request,

            "referee": referee,

        },

    )

    response["Cache-Control"] = "private, no-store, max-age=0"

    response["Pragma"] = "no-cache"

    return response

# ---------------------------------------------------------------------------

# STAFF DASHBOARD

# ---------------------------------------------------------------------------

@staff_required

def staff_dashboard(request: HttpRequest) -> HttpResponse:

    """

    Render the private staff dashboard.

    Provides the triage context the template expects:

    * ``pending_requests`` — awaiting review, most recent first

    * ``active_grants`` — live, non-revoked, in-window grants

    * ``recent_logs`` — last 20 audit events

    """

    now = timezone.now()

    # Self-heal any grants whose window has already closed before we

    # render the "Active access" tab.

    expired_grants = (

        AccessGrant.objects

        .filter(is_active=True, expires_at__lte=now)

        .select_related("access_request")

    )

    for grant in expired_grants:

        grant.access_request.mark_expired(now=now)

    pending_requests = (

        AccessRequest.objects

        .select_related("employer")

        .filter(status=AccessRequest.Status.PENDING)

        .prefetch_related(

            "document_requests__document",

            "referee_requests__referee",

        )

        .order_by("-created_at")

    )

    active_grants = (

        AccessGrant.objects

        .select_related("access_request", "access_request__employer")

        .filter(

            is_active=True,

            revoked_at__isnull=True,

            starts_at__lte=now,

            expires_at__gt=now,

            access_request__status=AccessRequest.Status.APPROVED,

        )

        .order_by("expires_at")[:20]

    )

    recent_logs = (

        AccessLog.objects

        .select_related("employer", "access_request")

        .order_by("-created_at")[:20]

    )

    return render(

        request,

        "employer_portal/staff_dashboard.html",

        {

            "pending_requests": pending_requests,

            "active_grants": active_grants,

            "recent_logs": recent_logs,

        },

    )

@staff_required

def staff_request_detail(request: HttpRequest, request_id) -> HttpResponse:

    """Render a complete staff review record for one access request."""

    access_request = get_object_or_404(

        AccessRequest.objects.select_related("employer", "reviewed_by", "grant"),

        request_id=request_id,

    )

    # Optional "Assign to me" — triggered from the dashboard.

    if request.GET.get("assign_me") == "1":

        if access_request.status == AccessRequest.Status.PENDING:

            access_request.reviewed_by = request.user

            access_request.save(update_fields=["reviewed_by", "updated_at"])

            messages.success(request, "Request assigned to you.")

        return redirect(

            "employer_portal:staff_request_detail",

            request_id=access_request.request_id,

        )

    documents = _requested_documents_for_review(access_request)

    referees = _requested_referees_for_review(access_request)

    document_permissions = {

        row.document_id: row.approved

        for row in DocumentAccessRequest.objects.filter(access_request=access_request)

    }

    referee_permissions = {

        row.referee_id: row.approved

        for row in RefereeAccessRequest.objects.filter(access_request=access_request)

    }

    grant = getattr(access_request, "grant", None)

    # Self-heal on load.

    if (

        grant is not None

        and grant.is_active

        and grant.expires_at <= timezone.now()

    ):

        access_request.mark_expired()

        access_request.refresh_from_db()

        grant.refresh_from_db()

    logs = (

        AccessLog.objects

        .filter(access_request=access_request)

        .order_by("-created_at")[:50]

    )

    return render(

        request,

        "employer_portal/staff_request_detail.html",

        {

            "access_request": access_request,

            "documents": documents,

            "referees": referees,

            "document_permissions": document_permissions,

            "referee_permissions": referee_permissions,

            "grant": grant,

            "logs": logs,

        },

    )

@require_POST

@staff_required

def approve_request(request: HttpRequest, request_id) -> HttpResponse:

    """Approve a pending request and issue a temporary access grant."""

    access_request = get_object_or_404(

        AccessRequest.objects.select_related("employer"),

        request_id=request_id,

    )

    if access_request.status != AccessRequest.Status.PENDING:

        messages.warning(

            request,

            "Only pending employer access requests can be approved.",

        )

        return redirect(

            "employer_portal:staff_request_detail",

            request_id=access_request.request_id,

        )

    now = timezone.now()

    expiry = now + timedelta(days=DEFAULT_ACCESS_DURATION_DAYS)

    with transaction.atomic():

        access_request = (

            AccessRequest.objects

            .select_for_update(of=("self",))

            .select_related("employer")

            .get(pk=access_request.pk)

        )

        try:

            grant = access_request.mark_approved(

                reviewer=request.user,

                expires_at=expiry,

                now=now,

            )

        except ValueError as exc:

            messages.warning(request, str(exc))

            return redirect(

                "employer_portal:staff_request_detail",

                request_id=access_request.request_id,

            )

    notification_sent, notification_error = _notify_employer_of_approval(

        request, access_request, grant

    )

    log_event(

        AccessLog.EventType.REQUEST_APPROVED,

        request,

        access_request=access_request,

        employer=access_request.employer,

        resource_type="access_request",

        resource_identifier=access_request.request_id,

        metadata={

            "reviewed_by": request.user.get_username(),

            "grant_token": str(grant.token),

            "starts_at": grant.starts_at.isoformat(),

            "expires_at": grant.expires_at.isoformat(),

            "access_duration_days": DEFAULT_ACCESS_DURATION_DAYS,

            "employer_notification_sent": notification_sent,

            **(

                {"employer_notification_error": notification_error}

                if notification_error

                else {}

            ),

        },

    )

    messages.success(

        request,

        (

            "Access approved successfully. "

            f"The private portal is active for {DEFAULT_ACCESS_DURATION_DAYS} days."

        ),

    )

    return redirect(

        "employer_portal:staff_request_detail",

        request_id=access_request.request_id,

    )

@require_POST

@staff_required

def reject_request(request: HttpRequest, request_id) -> HttpResponse:

    """Reject a pending request and disable any associated grant."""

    access_request = get_object_or_404(

        AccessRequest.objects.select_related("employer"),

        request_id=request_id,

    )

    if access_request.status != AccessRequest.Status.PENDING:

        messages.warning(

            request,

            "Only pending employer access requests can be rejected.",

        )

        return redirect(

            "employer_portal:staff_request_detail",

            request_id=access_request.request_id,

        )

    now = timezone.now()

    with transaction.atomic():

        access_request = (

            AccessRequest.objects

            .select_for_update(of=("self",))
            .select_related("employer")

            .get(pk=access_request.pk)

        )

        try:

            access_request.mark_rejected(reviewer=request.user, now=now)

        except ValueError as exc:

            messages.warning(request, str(exc))

            return redirect(

                "employer_portal:staff_request_detail",

                request_id=access_request.request_id,

            )

    log_event(

        AccessLog.EventType.REQUEST_REJECTED,

        request,

        access_request=access_request,

        employer=access_request.employer,

        resource_type="access_request",

        resource_identifier=access_request.request_id,

        metadata={"reviewed_by": request.user.get_username()},

    )

    messages.success(request, "The employer access request has been rejected.")

    return redirect(

        "employer_portal:staff_request_detail",

        request_id=access_request.request_id,

    )

@require_POST

@staff_required

def revoke_access(request: HttpRequest, request_id) -> HttpResponse:

    """Immediately revoke an active employer access grant."""

    access_request = get_object_or_404(

        AccessRequest.objects.select_related("employer"),

        request_id=request_id,

    )

    now = timezone.now()

    with transaction.atomic():

        access_request = (

            AccessRequest.objects

            .select_for_update(of=("self",))
            .select_related("employer")

            .get(pk=access_request.pk)

        )

        grant = (

            AccessGrant.objects

            .select_for_update()

            .filter(access_request=access_request, is_active=True)

            .first()

        )

        if grant is None:

            messages.warning(

                request,

                "There is no active access grant to revoke.",

            )

            return redirect(

                "employer_portal:staff_request_detail",

                request_id=access_request.request_id,

            )

        try:

            access_request.mark_revoked(reviewer=request.user, now=now)

        except ValueError as exc:

            messages.warning(request, str(exc))

            return redirect(

                "employer_portal:staff_request_detail",

                request_id=access_request.request_id,

            )

    log_event(

        AccessLog.EventType.ACCESS_REVOKED,

        request,

        access_request=access_request,

        employer=access_request.employer,

        resource_type="access_grant",

        resource_identifier=grant.pk,

        metadata={

            "revoked_by": request.user.get_username(),

            "grant_token": str(grant.token),

        },

    )

    messages.success(request, "Employer portal access has been revoked.")

    return redirect(

        "employer_portal:staff_request_detail",

        request_id=access_request.request_id,

    )