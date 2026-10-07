"""
Database models for the employer access portal.

The portal is designed around controlled access to professional documents and
referee information. Private documents are stored outside the public static
asset directories and are intended to be served only through authenticated,
authorised Django views.
"""

from __future__ import annotations

import uuid
from pathlib import Path
from typing import Any

from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.db import models, transaction
from django.utils import timezone


# ---------------------------------------------------------------------------
# PRIVATE DOCUMENT STORAGE
# ---------------------------------------------------------------------------

ALLOWED_DOCUMENT_EXTENSIONS = frozenset(
    {
        ".pdf", ".doc", ".docx", ".odt", ".rtf", ".txt",
        ".jpg", ".jpeg", ".png", ".webp", ".heic", ".heif",
    }
)


class PrivateDocumentStorage(FileSystemStorage):
    """Filesystem storage for private documents that refuses to build URLs."""

    def __init__(self, *args, **kwargs) -> None:
        kwargs.setdefault("location", settings.PRIVATE_DOCUMENTS_ROOT)
        kwargs.setdefault("base_url", None)
        super().__init__(*args, **kwargs)

    def url(self, name: str) -> str:  # pragma: no cover
        raise NotImplementedError(
            "Private documents are not addressable by URL. "
            "Serve them through an authorised Django view."
        )


PRIVATE_DOCUMENT_STORAGE = PrivateDocumentStorage()


def private_document_upload_path(instance: "Document", filename: str) -> str:
    suffix = Path(filename).suffix.lower()
    if suffix not in ALLOWED_DOCUMENT_EXTENSIONS:
        suffix = ".bin"
    document_type = getattr(instance, "document_type", None) or "other"
    return f"professional_documents/{document_type}/{uuid.uuid4().hex}{suffix}"


# ---------------------------------------------------------------------------
# SHARED HELPERS
# ---------------------------------------------------------------------------


def client_ip(request) -> str | None:
    """
    Return the best-guess client IP for a request, honouring proxies.

    The ``X-Forwarded-For`` header is only trusted when the deployment
    explicitly opts in via ``settings.TRUST_X_FORWARDED_FOR``.
    """
    if getattr(settings, "TRUST_X_FORWARDED_FOR", False):
        forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
        if forwarded:
            return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


def truncated_user_agent(request, *, limit: int = 512) -> str:
    return (request.META.get("HTTP_USER_AGENT") or "")[:limit]


# ---------------------------------------------------------------------------
# QUERY MANAGERS
# ---------------------------------------------------------------------------


class EmployerQuerySet(models.QuerySet):
    def active(self):
        return self.filter(is_active=True)

    def verified(self):
        return self.filter(is_verified=True)


class DocumentQuerySet(models.QuerySet):
    def active(self):
        return self.filter(is_active=True)


class AccessRequestQuerySet(models.QuerySet):
    def pending(self):
        return self.filter(status=AccessRequest.Status.PENDING)

    def approved(self):
        return self.filter(status=AccessRequest.Status.APPROVED)

    def terminal(self):
        return self.filter(status__in=AccessRequest.TERMINAL_STATUSES)

    def currently_approved(self):
        now = timezone.now()
        return self.filter(
            status=AccessRequest.Status.APPROVED,
            grant__is_active=True,
            grant__revoked_at__isnull=True,
            grant__starts_at__lte=now,
            grant__expires_at__gt=now,
        )

    def with_relations(self):
        return self.select_related(
            "employer", "reviewed_by", "grant"
        ).prefetch_related(
            "document_requests__document",
            "referee_requests__referee",
        )


class AccessGrantQuerySet(models.QuerySet):
    def active(self):
        now = timezone.now()
        return self.filter(
            is_active=True,
            revoked_at__isnull=True,
            starts_at__lte=now,
            expires_at__gt=now,
        )

    def expiring_within(self, days: int):
        now = timezone.now()
        return self.active().filter(expires_at__lte=now + timezone.timedelta(days=days))

    def expired(self):
        return self.filter(expires_at__lte=timezone.now())


class AccessLogQuerySet(models.QuerySet):
    def recent(self, limit: int = 10):
        return self.order_by("-created_at")[:limit]

    def for_dashboard(self):
        return self.select_related("employer", "access_request")

    def review_events(self):
        """Events that constitute a review decision on a request."""
        return self.filter(
            event_type__in=[
                AccessLog.EventType.REQUEST_APPROVED,
                AccessLog.EventType.REQUEST_REJECTED,
                AccessLog.EventType.REQUEST_EXPIRED,
                AccessLog.EventType.REQUEST_REOPENED,
                AccessLog.EventType.ACCESS_REVOKED,
            ]
        )


# ---------------------------------------------------------------------------
# EMPLOYERS
# ---------------------------------------------------------------------------


class Employer(models.Model):
    company_name = models.CharField(max_length=200)
    contact_name = models.CharField(max_length=150)
    job_title = models.CharField(max_length=150, blank=True)
    email = models.EmailField()
    phone = models.CharField(max_length=40, blank=True)
    company_website = models.URLField(blank=True)
    is_verified = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = EmployerQuerySet.as_manager()

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "employer"
        verbose_name_plural = "employers"
        indexes = [
            models.Index(fields=["email"], name="employer_email_idx"),
            models.Index(fields=["company_name"], name="employer_company_idx"),
            models.Index(fields=["is_active", "created_at"], name="employer_active_created_idx"),
            models.Index(fields=["is_verified", "is_active"], name="employer_verified_active_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.contact_name} — {self.company_name}"

    @property
    def display_name(self) -> str:
        return f"{self.contact_name} ({self.company_name})"


# ---------------------------------------------------------------------------
# DOCUMENTS
# ---------------------------------------------------------------------------


class Document(models.Model):
    class DocumentType(models.TextChoices):
        CV = "cv", "CV"
        ACADEMIC = "academic", "Academic Certificate"
        PROFESSIONAL = "professional", "Professional Certificate"
        SUPPORTING = "supporting", "Supporting Document"
        OTHER = "other", "Other"

    document_type = models.CharField(max_length=30, choices=DocumentType.choices)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    file = models.FileField(
        upload_to=private_document_upload_path,
        storage=PRIVATE_DOCUMENT_STORAGE,
        max_length=255,
    )
    version = models.PositiveIntegerField(default=1)
    is_active = models.BooleanField(default=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = DocumentQuerySet.as_manager()

    class Meta:
        ordering = ["document_type", "-uploaded_at"]
        indexes = [
            models.Index(fields=["document_type", "is_active"], name="doc_type_active_idx"),
            models.Index(fields=["is_active", "updated_at"], name="doc_active_updated_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.get_document_type_display()} — {self.title}"


# ---------------------------------------------------------------------------
# REFEREES
# ---------------------------------------------------------------------------


class Referee(models.Model):
    name = models.CharField(max_length=150)
    job_title = models.CharField(max_length=150)
    organisation = models.CharField(max_length=200)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=40, blank=True)
    relationship = models.CharField(max_length=150, blank=True)
    notes = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        indexes = [
            models.Index(fields=["is_active"], name="referee_active_idx"),
            models.Index(fields=["organisation", "is_active"], name="referee_org_active_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.name} — {self.organisation}"


# ---------------------------------------------------------------------------
# ACCESS REQUEST
# ---------------------------------------------------------------------------


class AccessRequest(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"
        EXPIRED = "expired", "Expired"
        REVOKED = "revoked", "Revoked"

    # Terminal states cannot be reached out of the normal flow, but staff
    # can reopen or reapprove them. See ``can_transition_to``.
    TERMINAL_STATUSES = frozenset({Status.REJECTED, Status.EXPIRED, Status.REVOKED})

    request_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    employer = models.ForeignKey(
        Employer,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="access_requests",
    )

    requester_name = models.CharField(max_length=150)
    requester_email = models.EmailField()
    requester_company = models.CharField(max_length=200)
    requester_job_title = models.CharField(max_length=150, blank=True)
    requester_phone = models.CharField(max_length=40, blank=True)
    reason = models.TextField(
        help_text="Why the requester needs access to the private material.",
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
    )

    requested_documents = models.ManyToManyField(
        Document,
        through="DocumentAccessRequest",
        blank=True,
        related_name="access_requests",
    )
    requested_referees = models.ManyToManyField(
        Referee,
        through="RefereeAccessRequest",
        blank=True,
        related_name="access_requests",
    )

    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_employer_access_requests",
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)

    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = AccessRequestQuerySet.as_manager()

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status", "created_at"], name="ar_status_created_idx"),
            models.Index(fields=["status", "expires_at"], name="ar_status_expires_idx"),
            models.Index(fields=["requester_email"], name="ar_email_idx"),
            models.Index(fields=["request_id"], name="ar_request_id_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.requester_name} — {self.requester_company} — {self.status}"

    # ------------------------------------------------------------------
    # STATUS
    # ------------------------------------------------------------------
    @property
    def is_terminal(self) -> bool:
        return self.status in self.TERMINAL_STATUSES

    def can_transition_to(self, new_status: str) -> bool:
        """
        Return whether the request may transition to ``new_status``.

        Terminal states (``REJECTED``, ``EXPIRED``, ``REVOKED``) may be
        reopened to ``PENDING`` for re-review, or directly reapproved.
        They cannot be re-rejected, re-revoked, or re-expired.
        """
        allowed = {
            self.Status.PENDING: {self.Status.APPROVED, self.Status.REJECTED},
            self.Status.APPROVED: {self.Status.EXPIRED, self.Status.REVOKED},
            # Staff-driven reversals of terminal states.
            self.Status.REJECTED: {self.Status.PENDING, self.Status.APPROVED},
            self.Status.EXPIRED: {self.Status.PENDING, self.Status.APPROVED},
            self.Status.REVOKED: {self.Status.PENDING, self.Status.APPROVED},
        }
        return new_status in allowed.get(self.status, set())

    # ------------------------------------------------------------------
    # LIVE-ACCESS CHECK
    # ------------------------------------------------------------------
    @property
    def is_currently_approved(self) -> bool:
        if self.status != self.Status.APPROVED:
            return False

        grant = self.__dict__.get("grant")
        if grant is None:
            try:
                grant = self.grant
            except AccessGrant.DoesNotExist:
                return False
        return grant.is_currently_active

    # ------------------------------------------------------------------
    # LAST ACTION
    # ------------------------------------------------------------------
    @property
    def last_review_log(self) -> "AccessLog | None":
        """
        Return the most recent review-decision audit row for this request.

        Filters to the events that constitute a review action (approve,
        reject, expire, reopen, revoke) so the admin can present a
        "who did what, when" summary without exposing ordinary views.
        """
        return (
            self.access_logs
            .review_events()
            .order_by("-created_at")
            .first()
        )

    # ------------------------------------------------------------------
    # DOMAIN MUTATIONS
    # ------------------------------------------------------------------
    @transaction.atomic
    def mark_approved(self, *, reviewer, expires_at, now=None) -> "AccessGrant":
        """
        Approve the request, mark its requested resources approved, and
        upsert the ``AccessGrant``. Returns the grant.

        Works from any non-approved state (pending, rejected, expired,
        revoked) so it doubles as the reapprove path.
        """
        now = now or timezone.now()
        if not self.can_transition_to(self.Status.APPROVED):
            raise ValueError(
                f"Cannot approve a request in status {self.status!r}."
            )

        self.status = self.Status.APPROVED
        self.reviewed_by = reviewer
        self.reviewed_at = now
        self.approved_at = now
        self.expires_at = expires_at
        self.save(
            update_fields=[
                "status", "reviewed_by", "reviewed_at",
                "approved_at", "expires_at", "updated_at",
            ]
        )

        self.document_requests.update(approved=True)
        self.referee_requests.update(approved=True)

        grant, _ = AccessGrant.objects.update_or_create(
            access_request=self,
            defaults={
                "starts_at": now,
                "expires_at": expires_at,
                "is_active": True,
                "revoked_at": None,
            },
        )
        return grant

    @transaction.atomic
    def mark_rejected(self, *, reviewer, now=None) -> None:
        now = now or timezone.now()
        if not self.can_transition_to(self.Status.REJECTED):
            raise ValueError(f"Cannot reject a request in status {self.status!r}.")

        self.status = self.Status.REJECTED
        self.reviewed_by = reviewer
        self.reviewed_at = now
        self.save(update_fields=["status", "reviewed_by", "reviewed_at", "updated_at"])

        AccessGrant.objects.filter(access_request=self, is_active=True).update(
            is_active=False, revoked_at=now
        )

    @transaction.atomic
    def mark_revoked(self, *, reviewer, now=None) -> None:
        now = now or timezone.now()
        if not self.can_transition_to(self.Status.REVOKED):
            raise ValueError(f"Cannot revoke a request in status {self.status!r}.")

        self.status = self.Status.REVOKED
        self.reviewed_by = reviewer
        self.reviewed_at = now
        self.save(update_fields=["status", "reviewed_by", "reviewed_at", "updated_at"])

        AccessGrant.objects.filter(access_request=self, is_active=True).update(
            is_active=False, revoked_at=now
        )

    @transaction.atomic
    def mark_expired(self, *, now=None) -> None:
        """Idempotent — used by the automated expiry management command."""
        now = now or timezone.now()
        if self.status != self.Status.APPROVED:
            return

        self.status = self.Status.EXPIRED
        self.save(update_fields=["status", "updated_at"])

        AccessGrant.objects.filter(access_request=self, is_active=True).update(
            is_active=False, revoked_at=now
        )

    @transaction.atomic
    def mark_reopened(self, *, reviewer, now=None) -> None:
        """
        Return a terminal request to ``PENDING`` for staff re-review.

        Deactivates any lingering grant so no portal access survives the
        reopen. Idempotent for already-pending requests (no-op).
        """
        now = now or timezone.now()
        if self.status == self.Status.PENDING:
            return

        if not self.can_transition_to(self.Status.PENDING):
            raise ValueError(
                f"Cannot reopen a request in status {self.status!r}."
            )

        self.status = self.Status.PENDING
        self.reviewed_by = reviewer
        self.reviewed_at = now
        # Clear the previous decision's timestamps so the pending row
        # does not display stale approval/expiry data.
        self.approved_at = None
        self.expires_at = None
        self.save(
            update_fields=[
                "status", "reviewed_by", "reviewed_at",
                "approved_at", "expires_at", "updated_at",
            ]
        )

        AccessGrant.objects.filter(access_request=self, is_active=True).update(
            is_active=False, revoked_at=now
        )


# ---------------------------------------------------------------------------
# REQUESTED DOCUMENTS
# ---------------------------------------------------------------------------


class DocumentAccessRequest(models.Model):
    access_request = models.ForeignKey(
        AccessRequest,
        on_delete=models.CASCADE,
        related_name="document_requests",
    )
    document = models.ForeignKey(
        Document,
        on_delete=models.PROTECT,
        related_name="access_request_items",
    )
    approved = models.BooleanField(default=False)
    viewed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["access_request", "document"],
                name="unique_request_document",
            ),
        ]
        indexes = [
            models.Index(fields=["access_request", "approved"], name="dar_req_approved_idx"),
            models.Index(fields=["document", "approved"], name="dar_doc_approved_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.access_request} → {self.document}"

    def mark_viewed(self, *, now=None) -> None:
        self.viewed_at = now or timezone.now()
        self.save(update_fields=["viewed_at"])


# ---------------------------------------------------------------------------
# REQUESTED REFEREES
# ---------------------------------------------------------------------------


class RefereeAccessRequest(models.Model):
    access_request = models.ForeignKey(
        AccessRequest,
        on_delete=models.CASCADE,
        related_name="referee_requests",
    )
    referee = models.ForeignKey(
        Referee,
        on_delete=models.PROTECT,
        related_name="access_request_items",
    )
    approved = models.BooleanField(default=False)
    viewed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["access_request", "referee"],
                name="unique_request_referee",
            ),
        ]
        indexes = [
            models.Index(fields=["access_request", "approved"], name="rar_req_approved_idx"),
            models.Index(fields=["referee", "approved"], name="rar_ref_approved_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.access_request} → {self.referee}"

    def mark_viewed(self, *, now=None) -> None:
        self.viewed_at = now or timezone.now()
        self.save(update_fields=["viewed_at"])


# ---------------------------------------------------------------------------
# ACCESS GRANTS
# ---------------------------------------------------------------------------


class AccessGrant(models.Model):
    access_request = models.OneToOneField(
        AccessRequest,
        on_delete=models.CASCADE,
        related_name="grant",
    )
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    starts_at = models.DateTimeField()
    expires_at = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    revoked_at = models.DateTimeField(null=True, blank=True)

    objects = AccessGrantQuerySet.as_manager()

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(expires_at__gt=models.F("starts_at")),
                name="grant_expires_after_start",
            ),
        ]
        indexes = [
            models.Index(fields=["token", "is_active"], name="grant_token_active_idx"),
            models.Index(fields=["is_active", "expires_at"], name="grant_active_expires_idx"),
            models.Index(fields=["expires_at"], name="grant_expires_idx"),
            models.Index(fields=["revoked_at", "expires_at"], name="grant_revoked_expires_idx"),
        ]

    def __str__(self) -> str:
        return f"Access grant for {self.access_request}"

    @property
    def is_currently_active(self) -> bool:
        if not self.is_active or self.revoked_at is not None:
            return False
        now = timezone.now()
        return self.starts_at <= now < self.expires_at

    @property
    def is_expired(self) -> bool:
        return self.expires_at <= timezone.now()


# ---------------------------------------------------------------------------
# ACCESS / VISITOR LOGS
# ---------------------------------------------------------------------------


class AccessLog(models.Model):
    class EventType(models.TextChoices):
        # Request lifecycle
        REQUEST_SUBMITTED = "request_submitted", "Access Request Submitted"
        REQUEST_APPROVED = "request_approved", "Access Request Approved"
        REQUEST_REJECTED = "request_rejected", "Access Request Rejected"
        REQUEST_EXPIRED = "request_expired", "Access Request Expired"
        REQUEST_REOPENED = "request_reopened", "Access Request Reopened"

        # Portal + resource access
        PORTAL_VIEWED = "portal_viewed", "Employer Portal Viewed"
        DOCUMENT_VIEWED = "document_viewed", "Document Viewed"
        DOCUMENT_DOWNLOADED = "document_downloaded", "Document Downloaded"
        REFEREE_VIEWED = "referee_viewed", "Referee Details Viewed"

        # Contact + grant lifecycle
        CONTACT_SUBMITTED = "contact_submitted", "Contact Form Submitted"
        ACCESS_GRANTED = "access_granted", "Access Granted"
        ACCESS_REVOKED = "access_revoked", "Access Revoked"
        ACCESS_EXPIRED = "access_expired", "Access Expired"

        # Staff
        LOGIN = "login", "Staff Login"
        LOGOUT = "logout", "Staff Logout"

    employer = models.ForeignKey(
        Employer,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="access_logs",
    )
    access_request = models.ForeignKey(
        AccessRequest,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="access_logs",
    )
    event_type = models.CharField(max_length=40, choices=EventType.choices)
    resource_type = models.CharField(max_length=50, blank=True)
    resource_identifier = models.CharField(max_length=255, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = AccessLogQuerySet.as_manager()

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["event_type", "created_at"], name="log_event_created_idx"),
            models.Index(fields=["employer", "created_at"], name="log_employer_created_idx"),
            models.Index(fields=["access_request", "created_at"], name="log_request_created_idx"),
            models.Index(fields=["resource_type", "created_at"], name="log_res_created_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.event_type} — {self.created_at:%Y-%m-%d %H:%M}"

    @classmethod
    def log_from_request(
        cls,
        request,
        event_type: str,
        *,
        employer: Employer | None = None,
        access_request: AccessRequest | None = None,
        resource_type: str = "",
        resource_identifier: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> "AccessLog":
        meta = dict(metadata or {})
        user = getattr(request, "user", None)
        if user is not None and getattr(user, "is_authenticated", False):
            meta.setdefault("actor", user.get_username())

        return cls.objects.create(
            employer=employer or getattr(access_request, "employer", None),
            access_request=access_request,
            event_type=event_type,
            resource_type=resource_type,
            resource_identifier=resource_identifier,
            ip_address=client_ip(request),
            user_agent=truncated_user_agent(request),
            metadata=meta,
        )

    @property
    def actor_label(self) -> str:
        if self.access_request_id:
            ar = self.access_request
            name = ar.requester_name or ""
            company = ar.requester_company or ""
            label = " · ".join(x for x in (name, company) if x)
            return label or str(ar.request_id)
        if self.employer_id:
            return self.employer.company_name
        return "System"

    @property
    def reviewer_username(self) -> str:
        """
        Return the username of the staff member who performed this action.

        Prefers the explicit ``reviewed_by`` / ``revoked_by`` metadata
        keys the admin and staff views write; falls back to the generic
        ``actor`` key, then to an empty string.
        """
        meta = self.metadata or {}
        for key in ("revoked_by", "reviewed_by", "actor"):
            value = meta.get(key)
            if value:
                return str(value)
        return ""