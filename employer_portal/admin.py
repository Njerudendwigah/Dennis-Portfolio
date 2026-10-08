"""
Django admin configuration for the employer access portal (Unfold theme).
The admin is the private control centre for:
- employer records
- professional documents
- referees
- access requests
- access grants
- audit logs
Setup:
    pip install django-unfold
    Add "unfold" BEFORE "django.contrib.admin" in INSTALLED_APPS.
Dashboard wiring:
    The staff dashboard template expects a context dict produced by
    ``DashboardDataProvider``. Your view should look like::
        from .admin import DashboardDataProvider
        class StaffDashboardView(StaffRequiredMixin, TemplateView):
            template_name = "admin/employer_portal/dashboard.html"
            def get_context_data(self, **kwargs):
                ctx = super().get_context_data(**kwargs)
                provider = DashboardDataProvider(self.request)
                ctx.update(provider.build())
                return ctx
    Every context key the template reads is documented on
    ``DashboardDataProvider`` — nothing else is required.
"""
from __future__ import annotations

import csv
import hashlib
import hmac
from datetime import timedelta

from django.conf import settings
from django.contrib import admin, messages
from django.contrib.auth.admin import GroupAdmin as BaseGroupAdmin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import Group, User
from django.db import models, transaction
from django.db.models import QuerySet
from django.http import HttpResponse
from django.urls import reverse
from django.utils import timezone
from unfold.admin import ModelAdmin, TabularInline
from unfold.contrib.filters.admin import RangeDateFilter
from unfold.decorators import action, display
from unfold.forms import (
    AdminPasswordChangeForm,
    UserChangeForm,
    UserCreationForm,
)
from unfold.widgets import UnfoldAdminFileFieldWidget

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

DEFAULT_GRANT_DAYS = 7
EXPIRING_SOON_DAYS = 7
DASHBOARD_RECENT_LIMIT = 5
DASHBOARD_ACTIVITY_LIMIT = 10
REQUEST_STATUS_COLORS = {
    AccessRequest.Status.PENDING: "warning",
    AccessRequest.Status.APPROVED: "success",
    AccessRequest.Status.REJECTED: "danger",
    AccessRequest.Status.EXPIRED: "info",
    AccessRequest.Status.REVOKED: "danger",
}
REQUEST_STATUS_CLASSES = {
    AccessRequest.Status.PENDING:  "bg-amber-50 text-amber-700 dark:bg-amber-500/10 dark:text-amber-300",
    AccessRequest.Status.APPROVED: "bg-emerald-50 text-emerald-700 dark:bg-emerald-500/10 dark:text-emerald-300",
    AccessRequest.Status.REJECTED: "bg-rose-50 text-rose-700 dark:bg-rose-500/10 dark:text-rose-300",
    AccessRequest.Status.EXPIRED:  "bg-slate-100 text-slate-600 dark:bg-slate-500/10 dark:text-slate-300",
    AccessRequest.Status.REVOKED:  "bg-rose-50 text-rose-700 dark:bg-rose-500/10 dark:text-rose-300",
}
EVENT_ICONS = {
    getattr(AccessLog.EventType, name, name): icon
    for name, icon in (
        ("REQUEST_CREATED",   "add_circle"),
        ("REQUEST_APPROVED",  "task_alt"),
        ("REQUEST_REJECTED",  "cancel"),
        ("ACCESS_GRANTED",    "key"),
        ("ACCESS_REVOKED",    "key_off"),
        ("ACCESS_EXPIRED",    "schedule"),
        ("DOCUMENT_VIEWED",   "visibility"),
        ("REFEREE_VIEWED",    "visibility"),
        ("LOGIN",             "login"),
    )
}


class PrivateFileInput(UnfoldAdminFileFieldWidget):
    """
    File input that never renders a link to the stored private file.
    Private documents are deliberately not addressable by URL (the
    private storage raises ``NotImplementedError`` from ``.url``), so the
    stock "Currently: <link>" block would crash the admin change page.
    Skipping the initial-value block keeps the plain file chooser, and
    leaving it empty on save keeps the existing file.
    """
    def is_initial(self, value):
        return False


class PortalModelAdmin(ModelAdmin):
    """Shared Unfold behaviour for every model in the portal."""
    list_filter_submit = True
    compressed_fields = True
    warn_unsaved_form = True
    list_per_page = 25
    save_on_top = True
    show_full_result_count = True
    def log_action(
        self,
        request,
        access_request: AccessRequest | None = None,
        event_type: str | None = None,
        *,
        employer: Employer | None = None,
        resource_type: str = "",
        resource_identifier: str = "",
        metadata: dict | None = None,
    ) -> AccessLog | None:
        """
        Create an ``AccessLog`` row for a staff action.
        Captures the reviewer's IP and user-agent — the original
        implementation silently dropped both.
        """
        if event_type is None:
            return None
        meta = dict(metadata or {})
        meta.setdefault("actioned_by", request.user.get_username())
        return AccessLog.objects.create(
            employer=employer or getattr(access_request, "employer", None),
            access_request=access_request,
            event_type=event_type,
            resource_type=resource_type,
            resource_identifier=resource_identifier,
            ip_address=self._client_ip(request),
            user_agent=(request.META.get("HTTP_USER_AGENT") or "")[:512],
            metadata=meta,
        )

    @staticmethod
    def _client_ip(request) -> str | None:
        forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.META.get("REMOTE_ADDR")


class PendingOnlyFilter(admin.SimpleListFilter):
    title = "pending review"
    parameter_name = "pending"
    def lookups(self, request, model_admin):
        return (("1", "Pending only"),)
    def queryset(self, request, queryset):
        if self.value() == "1":
            return queryset.filter(status=AccessRequest.Status.PENDING)
        return queryset


class ExpiringSoonFilter(admin.SimpleListFilter):
    title = "expiring soon"
    parameter_name = "expiring"
    def lookups(self, request, model_admin):
        return (("7", "Next 7 days"), ("1", "Next 24 hours"))
    def queryset(self, request, queryset):
        if not self.value():
            return queryset
        now = timezone.now()
        window = now + timedelta(days=int(self.value()))
        return queryset.filter(
            status=AccessRequest.Status.APPROVED,
            expires_at__gte=now,
            expires_at__lte=window,
        )


class DocumentAccessRequestInline(TabularInline):
    model = DocumentAccessRequest
    extra = 0
    autocomplete_fields = ("document",)
    fields = ("document", "approved", "viewed_at")
    readonly_fields = ("viewed_at",)
    verbose_name = "Requested document"
    verbose_name_plural = "Requested documents"


class RefereeAccessRequestInline(TabularInline):
    model = RefereeAccessRequest
    extra = 0
    autocomplete_fields = ("referee",)
    fields = ("referee", "approved", "viewed_at")
    readonly_fields = ("viewed_at",)
    verbose_name = "Requested referee"
    verbose_name_plural = "Requested referees"


@admin.register(Employer)


class EmployerAdmin(PortalModelAdmin):
    list_display = (
        "company_name",
        "contact_name",
        "job_title",
        "email",
        "verification_badge",
        "is_active",
        "created_at",
    )
    list_filter = (
        "is_verified",
        "is_active",
        ("created_at", RangeDateFilter),
    )
    search_fields = (
        "company_name",
        "contact_name",
        "job_title",
        "email",
        "phone",
    )
    ordering = ("-created_at",)
    readonly_fields = ("created_at", "updated_at")
    actions = ("mark_verified", "mark_unverified")
    fieldsets = (
        (
            "Employer identity",
            {
                "fields": (
                    "company_name",
                    "contact_name",
                    "job_title",
                    "email",
                    "phone",
                    "company_website",
                )
            },
        ),
        (
            "Portal status",
            {"fields": ("is_verified", "is_active", "notes")},
        ),
        (
            "Record timestamps",
            {"fields": ("created_at", "updated_at")},
        ),
    )
    def get_queryset(self, request):
        return super().get_queryset(request).select_related()

    @display(
        description="Verification",
        label={"Verified": "success", "Unverified": "warning"},
    )
    def verification_badge(self, obj):
        return "Verified" if obj.is_verified else "Unverified"

    @action(description="Mark selected employers as verified")
    def mark_verified(self, request, queryset):
        updated = queryset.update(is_verified=True, updated_at=timezone.now())
        self.message_user(request, f"{updated} employer(s) verified.", messages.SUCCESS)

    @action(description="Mark selected employers as unverified")
    def mark_unverified(self, request, queryset):
        updated = queryset.update(is_verified=False, updated_at=timezone.now())
        self.message_user(request, f"{updated} employer(s) unverified.", messages.WARNING)


@admin.register(Document)


class DocumentAdmin(PortalModelAdmin):
    list_display = (
        "title",
        "document_type",
        "version",
        "is_active",
        "uploaded_at",
        "updated_at",
    )
    list_filter = (
        "document_type",
        "is_active",
        ("uploaded_at", RangeDateFilter),
    )
    search_fields = ("title", "description")
    ordering = ("document_type", "-uploaded_at")
    readonly_fields = ("uploaded_at", "updated_at", "current_file")
    formfield_overrides = {
        models.FileField: {"widget": PrivateFileInput},
    }

    @display(description="Current file")
    def current_file(self, obj):
        """Show the stored filename only (never a link to the private file)."""
        if obj and obj.pk and obj.file:
            return obj.file.name.rsplit("/", 1)[-1]
        return "No file uploaded"
    fieldsets = (
        (
            "Private professional document",
            {
                "fields": (
                    "document_type",
                    "title",
                    "description",
                    "file",
                    "current_file",
                    "version",
                    "is_active",
                )
            },
        ),
        (
            "Record timestamps",
            {"fields": ("uploaded_at", "updated_at")},
        ),
    )


@admin.register(Referee)


class RefereeAdmin(PortalModelAdmin):
    list_display = (
        "name",
        "job_title",
        "organisation",
        "email",
        "phone",
        "is_active",
        "created_at",
    )
    list_filter = (
        "is_active",
        "organisation",
        ("created_at", RangeDateFilter),
    )
    search_fields = (
        "name",
        "job_title",
        "organisation",
        "email",
        "phone",
        "relationship",
    )
    ordering = ("name",)
    readonly_fields = ("created_at", "updated_at")
    fieldsets = (
        (
            "Referee details",
            {
                "fields": (
                    "name",
                    "job_title",
                    "organisation",
                    "relationship",
                    "email",
                    "phone",
                )
            },
        ),
        ("Internal notes", {"fields": ("notes", "is_active")}),
        ("Record timestamps", {"fields": ("created_at", "updated_at")}),
    )


@admin.register(AccessRequest)


class AccessRequestAdmin(PortalModelAdmin):
    list_display = (
        "requester_name",
        "requester_company",
        "requester_email",
        "status_badge",
        "created_at",
        "approved_at",
        "expires_at",
    )
    list_filter = (
        PendingOnlyFilter,
        ExpiringSoonFilter,
        "status",
        ("created_at", RangeDateFilter),
        ("approved_at", RangeDateFilter),
        ("expires_at", RangeDateFilter),
    )
    search_fields = (
        "request_id",
        "requester_name",
        "requester_email",
        "requester_company",
        "requester_job_title",
        "requester_phone",
        "reason",
    )
    ordering = ("-created_at",)
    date_hierarchy = "created_at"
    list_select_related = ("employer", "reviewed_by")
    autocomplete_fields = ("employer", "reviewed_by")
    inlines = (DocumentAccessRequestInline, RefereeAccessRequestInline)
    actions = ("approve_requests", "reject_requests", "revoke_requests", "renew_requests")
    readonly_fields = (
        "request_id",
        "created_at",
        "updated_at",
        "reviewed_at",
        "approved_at",
        "ip_address",
        "user_agent",
    )
    fieldsets = (
        (
            "Request",
            {
                "classes": ("tab",),
                "fields": ("request_id", "status", "reason"),
            },
        ),
        (
            "Requester",
            {
                "classes": ("tab",),
                "fields": (
                    "employer",
                    "requester_name",
                    "requester_email",
                    "requester_company",
                    "requester_job_title",
                    "requester_phone",
                ),
            },
        ),
        (
            "Review",
            {
                "classes": ("tab",),
                "fields": ("reviewed_by", "reviewed_at", "approved_at", "expires_at"),
            },
        ),
        (
            "Security",
            {
                "classes": ("tab",),
                "fields": ("ip_address", "user_agent", "created_at", "updated_at"),
            },
        ),
    )
    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related("employer", "reviewed_by")
            .prefetch_related("document_requests", "referee_requests")
        )

    @display(description="Status", label=REQUEST_STATUS_COLORS)
    def status_badge(self, obj):
        return obj.status, obj.get_status_display()

    @action(description="Approve selected pending requests (7-day access)")
    def approve_requests(self, request, queryset):
        now = timezone.now()
        expires = now + timedelta(days=DEFAULT_GRANT_DAYS)
        count = 0
        with transaction.atomic():
            pending = (
                queryset
                .filter(status=AccessRequest.Status.PENDING)
                .select_for_update()
            )
            for ar in pending:
                ar.status = AccessRequest.Status.APPROVED
                ar.reviewed_by = request.user
                ar.reviewed_at = now
                ar.approved_at = now
                ar.expires_at = expires
                ar.save(
                    update_fields=[
                        "status",
                        "reviewed_by",
                        "reviewed_at",
                        "approved_at",
                        "expires_at",
                        "updated_at",
                    ]
                )
                ar.document_requests.update(approved=True)
                ar.referee_requests.update(approved=True)
                AccessGrant.objects.update_or_create(
                    access_request=ar,
                    defaults={
                        "starts_at": now,
                        "expires_at": expires,
                        "is_active": True,
                        "revoked_at": None,
                    },
                )
                self.log_action(
                    request,
                    access_request=ar,
                    event_type=AccessLog.EventType.REQUEST_APPROVED,
                    resource_type="access_request",
                    resource_identifier=str(ar.request_id),
                    metadata={"expires_at": expires.isoformat()},
                )
                count += 1
        self.message_user(request, f"{count} request(s) approved.", messages.SUCCESS)

    @action(description="Reject selected pending requests")
    def reject_requests(self, request, queryset):
        now = timezone.now()
        count = 0
        with transaction.atomic():
            pending = (
                queryset
                .filter(status=AccessRequest.Status.PENDING)
                .select_for_update()
            )
            for ar in pending:
                ar.status = AccessRequest.Status.REJECTED
                ar.reviewed_by = request.user
                ar.reviewed_at = now
                ar.save(
                    update_fields=[
                        "status",
                        "reviewed_by",
                        "reviewed_at",
                        "updated_at",
                    ]
                )
                AccessGrant.objects.filter(
                    access_request=ar, is_active=True
                ).update(is_active=False, revoked_at=now)
                self.log_action(
                    request,
                    access_request=ar,
                    event_type=AccessLog.EventType.REQUEST_REJECTED,
                    resource_type="access_request",
                    resource_identifier=str(ar.request_id),
                )
                count += 1
        self.message_user(request, f"{count} request(s) rejected.", messages.WARNING)

    @action(description="Revoke access for selected approved requests")
    def revoke_requests(self, request, queryset):
        now = timezone.now()
        count = 0
        with transaction.atomic():
            approved = (
                queryset
                .filter(status=AccessRequest.Status.APPROVED)
                .select_for_update()
            )
            for ar in approved:
                ar.status = AccessRequest.Status.REVOKED
                ar.reviewed_by = request.user
                ar.reviewed_at = now
                ar.save(
                    update_fields=[
                        "status",
                        "reviewed_by",
                        "reviewed_at",
                        "updated_at",
                    ]
                )
                AccessGrant.objects.filter(
                    access_request=ar, is_active=True
                ).update(is_active=False, revoked_at=now)
                self.log_action(
                    request,
                    access_request=ar,
                    event_type=AccessLog.EventType.ACCESS_REVOKED,
                    resource_type="access_request",
                    resource_identifier=str(ar.request_id),
                )
                count += 1
        self.message_user(request, f"{count} request(s) revoked.", messages.WARNING)

    @action(description=f"Extend access by {DEFAULT_GRANT_DAYS} days")
    def renew_requests(self, request, queryset):
        now = timezone.now()
        extension = timedelta(days=DEFAULT_GRANT_DAYS)
        count = 0
        with transaction.atomic():
            active = (
                queryset
                .filter(status=AccessRequest.Status.APPROVED)
                .select_for_update()
            )
            for ar in active:
                baseline = max(ar.expires_at or now, now)
                ar.expires_at = baseline + extension
                ar.save(update_fields=["expires_at", "updated_at"])
                AccessGrant.objects.filter(
                    access_request=ar, is_active=True
                ).update(expires_at=ar.expires_at)
                self.log_action(
                    request,
                    access_request=ar,
                    event_type=AccessLog.EventType.ACCESS_GRANTED,
                    resource_type="access_request",
                    resource_identifier=str(ar.request_id),
                    metadata={"new_expires_at": ar.expires_at.isoformat()},
                )
                count += 1
        self.message_user(request, f"{count} request(s) extended.", messages.SUCCESS)


@admin.register(AccessGrant)


class AccessGrantAdmin(PortalModelAdmin):
    list_display = (
        "access_request",
        "state_badge",
        "starts_at",
        "expires_at",
        "is_active",
        "created_at",
        "revoked_at",
    )
    list_filter = (
        "is_active",
        ("starts_at", RangeDateFilter),
        ("expires_at", RangeDateFilter),
        ("created_at", RangeDateFilter),
    )
    search_fields = (
        "access_request__request_id",
        "access_request__requester_name",
        "access_request__requester_email",
        "access_request__requester_company",
    )
    ordering = ("-created_at",)
    readonly_fields = ("token_fingerprint", "created_at", "revoked_at")
    autocomplete_fields = ("access_request",)
    actions = ("revoke_grants", "extend_grants")
    list_select_related = ("access_request",)
    fieldsets = (
        (
            "Access grant",
            {
                "fields": (
                    "access_request",
                    "token_fingerprint",
                    "starts_at",
                    "expires_at",
                    "is_active",
                )
            },
        ),
        ("Revocation", {"fields": ("revoked_at",)}),
        ("Record timestamp", {"fields": ("created_at",)}),
    )
    def get_queryset(self, request):
        return super().get_queryset(request).select_related("access_request")

    @display(description="Token fingerprint")
    def token_fingerprint(self, obj):
        if not obj or not obj.token:
            return "Unavailable"
        return hmac.new(
            settings.SECRET_KEY.encode("utf-8"),
            str(obj.token).encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()[:16]

    @display(
        description="State",
        label={"Active": "success", "Expired": "info", "Revoked": "danger"},
    )
    def state_badge(self, obj):
        if obj.revoked_at:
            return "Revoked"
        if obj.expires_at <= timezone.now():
            return "Expired"
        if not obj.is_active:
            return "Inactive"
        return "Active"

    @action(description="Revoke selected active grants")
    def revoke_grants(self, request, queryset):
        now = timezone.now()
        count = 0
        with transaction.atomic():
            grants = (
                queryset
                .filter(is_active=True)
                .select_related("access_request")
                .select_for_update()
            )
            for grant in grants:
                grant.is_active = False
                grant.revoked_at = now
                grant.save(update_fields=["is_active", "revoked_at"])
                access_request = grant.access_request
                if access_request.status == AccessRequest.Status.APPROVED:
                    access_request.status = AccessRequest.Status.REVOKED
                    access_request.reviewed_at = now
                    access_request.save(
                        update_fields=["status", "reviewed_at", "updated_at"]
                    )
                    self.log_action(
                        request,
                        access_request=access_request,
                        event_type=AccessLog.EventType.ACCESS_REVOKED,
                        resource_type="access_grant",
                        resource_identifier=str(grant.pk),
                        metadata={"action": "revoke_grant"},
                    )
                count += 1
        self.message_user(request, f"{count} grant(s) revoked.", messages.WARNING)

    @action(description=f"Extend selected grants by {DEFAULT_GRANT_DAYS} days")
    def extend_grants(self, request, queryset):
        now = timezone.now()
        extension = timedelta(days=DEFAULT_GRANT_DAYS)
        count = 0
        with transaction.atomic():
            grants = (
                queryset
                .filter(is_active=True)
                .select_related("access_request")
                .select_for_update()
            )
            for grant in grants:
                baseline = max(grant.expires_at or now, now)
                grant.expires_at = baseline + extension
                grant.save(update_fields=["expires_at"])
                access_request = grant.access_request
                if access_request.status == AccessRequest.Status.APPROVED:
                    access_request.expires_at = grant.expires_at
                    access_request.save(update_fields=["expires_at", "updated_at"])
                self.log_action(
                    request,
                    access_request=access_request,
                    event_type=AccessLog.EventType.ACCESS_GRANTED,
                    resource_type="access_grant",
                    resource_identifier=str(grant.pk),
                    metadata={
                        "action": "extend_grant",
                        "new_expires_at": grant.expires_at.isoformat(),
                    },
                )
                count += 1
        self.message_user(request, f"{count} grant(s) extended.", messages.SUCCESS)
    def has_delete_permission(self, request, obj=None):
        """Keep access-grant history intact; use revoke instead of delete."""
        return False


@admin.register(AccessLog)


class AccessLogAdmin(PortalModelAdmin):
    list_display = (
        "created_at",
        "event_badge",
        "employer",
        "access_request",
        "resource_type",
        "resource_identifier",
        "ip_address",
    )
    list_filter = (
        "event_type",
        "resource_type",
        ("created_at", RangeDateFilter),
    )
    search_fields = (
        "event_type",
        "resource_type",
        "resource_identifier",
        "ip_address",
        "user_agent",
        "employer__company_name",
        "employer__contact_name",
        "employer__email",
        "access_request__requester_email",
        "access_request__requester_name",
    )
    ordering = ("-created_at",)
    list_per_page = 50
    date_hierarchy = "created_at"
    list_select_related = ("employer", "access_request")
    readonly_fields = (
        "created_at",
        "event_type",
        "employer",
        "access_request",
        "resource_type",
        "resource_identifier",
        "ip_address",
        "user_agent",
        "metadata",
    )
    fieldsets = (
        (
            "Activity",
            {
                "fields": (
                    "created_at",
                    "event_type",
                    "employer",
                    "access_request",
                )
            },
        ),
        (
            "Resource",
            {
                "fields": (
                    "resource_type",
                    "resource_identifier",
                    "metadata",
                )
            },
        ),
        (
            "Request metadata",
            {"fields": ("ip_address", "user_agent")},
        ),
    )
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            "employer", "access_request"
        )

    @display(description="Event")
    def event_badge(self, obj):
        icon = EVENT_ICONS.get(obj.event_type, "info")
        return f"{icon}  {obj.get_event_type_display()}"
    def has_add_permission(self, request):
        """Audit entries must be generated by application activity."""
        return False
    def has_change_permission(self, request, obj=None):
        """Audit entries are immutable."""
        return False
    def has_delete_permission(self, request, obj=None):
        """Audit entries cannot be deleted from Django Admin."""
        return False
admin.site.unregister(User)
admin.site.unregister(Group)


@admin.register(User)


class UserAdmin(BaseUserAdmin, ModelAdmin):
    form = UserChangeForm
    add_form = UserCreationForm
    change_password_form = AdminPasswordChangeForm
    list_filter_submit = True


@admin.register(Group)


class GroupAdmin(BaseGroupAdmin, ModelAdmin):
    pass


class DashboardDataProvider:
    """
    Build the full context dict the staff dashboard template expects.
    The template (``templates/admin/employer_portal/dashboard.html``)
    reads these keys and *only* these keys:
    ``kpis``                     list[dict]  – KPI cards
    ``recent_requests``          list[dict]  – latest access requests
    ``expiring_soon``            list[dict]  – grants approaching expiry
    ``recent_activity``          list[dict]  – audit events
    ``documents_count``          int
    ``pending_requests_count``   int
    ``activity_total``           int
    ``htmx_enabled``             bool        – enable live polling if HTMX present
    All list dicts are plain, JSON-serializable Python — safe to render,
    safe to reuse in an HTMX partial, safe to dump into a CSV export.
    """
    def __init__(self, request, *, htmx_enabled: bool = True):
        self.request = request
        self.htmx_enabled = htmx_enabled
    def build(self) -> dict:
        """Return the full context dict for the dashboard."""
        return {
            "kpis": self.kpis(),
            "recent_requests": self.recent_requests(),
            "expiring_soon": self.expiring_soon(),
            "recent_activity": self.recent_activity(),
            "documents_count": self.documents_count(),
            "pending_requests_count": self.pending_requests_count(),
            "activity_total": self.activity_total(),
            "htmx_enabled": self.htmx_enabled,
        }
    def activity_context(self) -> dict:
        """
        Subset used by the HTMX polling endpoint — returns the same
        keys the ``#epd-activity-region`` fragment expects.
        """
        return {
            "recent_activity": self.recent_activity(),
            "activity_total": self.activity_total(),
        }
    def kpis(self) -> list[dict]:
        now = timezone.now()
        week_ago = now - timedelta(days=7)
        two_weeks_ago = now - timedelta(days=14)
        expiry_window = now + timedelta(days=EXPIRING_SOON_DAYS)
        pending_qs = AccessRequest.objects.filter(status=AccessRequest.Status.PENDING)
        active_grants_qs = AccessGrant.objects.filter(
            is_active=True, expires_at__gt=now, revoked_at__isnull=True
        )
        expiring_qs = active_grants_qs.filter(expires_at__lte=expiry_window)
        pending_now = pending_qs.filter(created_at__gte=week_ago).count()
        pending_prev = pending_qs.filter(
            created_at__gte=two_weeks_ago, created_at__lt=week_ago
        ).count()
        approved_now = AccessRequest.objects.filter(
            status=AccessRequest.Status.APPROVED, approved_at__gte=week_ago
        ).count()
        approved_prev = AccessRequest.objects.filter(
            status=AccessRequest.Status.APPROVED,
            approved_at__gte=two_weeks_ago,
            approved_at__lt=week_ago,
        ).count()
        return [
            {
                "title": "Pending requests",
                "value": pending_qs.count(),
                "hint": f"{pending_now} new this week",
                "icon": "inbox",
                "href": reverse("admin:employer_portal_accessrequest_changelist")
                        + "?pending=1",
                "delta": self._delta_label(pending_now, pending_prev),
                "delta_direction": "up" if pending_now >= pending_prev else "down",
            },
            {
                "title": "Active grants",
                "value": active_grants_qs.count(),
                "hint": f"{expiring_qs.count()} expiring in {EXPIRING_SOON_DAYS} days",
                "icon": "key",
                "href": reverse("admin:employer_portal_accessgrant_changelist")
                        + "?is_active__exact=1",
            },
            {
                "title": "Approved this week",
                "value": approved_now,
                "hint": f"vs {approved_prev} last week",
                "icon": "task_alt",
                "href": reverse("admin:employer_portal_accessrequest_changelist")
                        + "?status__exact=approved",
                "delta": self._delta_label(approved_now, approved_prev),
                "delta_direction": "up" if approved_now >= approved_prev else "down",
            },
            {
                "title": "Documents",
                "value": self.documents_count(),
                "hint": "Active portfolio documents",
                "icon": "description",
                "href": reverse("admin:employer_portal_document_changelist")
                        + "?is_active__exact=1",
            },
        ]
    def recent_requests(self, limit: int = DASHBOARD_RECENT_LIMIT) -> list[dict]:
        qs = (
            AccessRequest.objects
            .select_related("employer", "reviewed_by")
            .order_by("-created_at")[:limit]
        )
        return [
            {
                "name": ar.requester_name,
                "company": ar.requester_company or "—",
                "status": ar.get_status_display(),
                "status_class": REQUEST_STATUS_CLASSES.get(ar.status, ""),
                "url": reverse(
                    "admin:employer_portal_accessrequest_change", args=[ar.pk]
                ),
                "created_at": ar.created_at,
                "assigned_to": getattr(ar, "reviewed_by", None),
                "can_assign": ar.status == AccessRequest.Status.PENDING,
            }
            for ar in qs
        ]
    def expiring_soon(
        self, days: int = EXPIRING_SOON_DAYS, limit: int = DASHBOARD_RECENT_LIMIT
    ) -> list[dict]:
        now = timezone.now()
        qs = (
            AccessGrant.objects
            .filter(
                is_active=True,
                revoked_at__isnull=True,
                expires_at__gt=now,
                expires_at__lte=now + timedelta(days=days),
            )
            .select_related("access_request")
            .order_by("expires_at")[:limit]
        )
        return [
            {
                "name": grant.access_request.requester_name,
                "company": grant.access_request.requester_company or "—",
                "expires_at": grant.expires_at,
            }
            for grant in qs
        ]
    def recent_activity(self, limit: int = DASHBOARD_ACTIVITY_LIMIT) -> list[dict]:
        qs = (
            AccessLog.objects
            .select_related("employer", "access_request")
            .order_by("-created_at")[:limit]
        )
        return [
            {
                "event": log.get_event_type_display(),
                "who": self._actor_label(log),
                "ip": log.ip_address or "",
                "created_at": log.created_at,
            }
            for log in qs
        ]
    def documents_count(self) -> int:
        return Document.objects.filter(is_active=True).count()
    def pending_requests_count(self) -> int:
        return AccessRequest.objects.filter(
            status=AccessRequest.Status.PENDING
        ).count()
    def activity_total(self) -> int:
        return AccessLog.objects.count()

    @staticmethod
    def _delta_label(current: int, previous: int) -> str:
        if previous == 0:
            return "new" if current else "0"
        pct = round(((current - previous) / previous) * 100)
        return f"{pct:+d}%"

    @staticmethod
    def _actor_label(log: AccessLog) -> str:
        """Human-readable 'who' string for an audit row."""
        if log.access_request_id:
            ar = log.access_request
            company = ar.requester_company or ""
            name = ar.requester_name or ""
            return f"{name} · {company}".strip(" ·") or str(ar.request_id)
        if log.employer_id:
            return log.employer.company_name
        return "System"


def _safe_csv_value(value) -> str:
    text = "" if value is None else str(value)
    if text.startswith(("=", "+", "-", "@")):
        return f"'{text}"
    return text


def _safe_download_filename(filename: str) -> str:
    cleaned = str(filename or "activity.csv").replace("\r", "").replace("\n", "")
    cleaned = cleaned.replace('"', "")
    cleaned = cleaned.rsplit("/", 1)[-1].rsplit("\\", 1)[-1]
    return cleaned or "activity.csv"


def export_activity_csv(queryset: QuerySet, *, filename: str = "activity.csv") -> HttpResponse:
    """
    Stream an ``AccessLog`` queryset as CSV.
    Wire into your dashboard view::
        if request.GET.get("format") == "csv":
            return export_activity_csv(
                AccessLog.objects.select_related("employer", "access_request")
            )
    """
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = (
        f'attachment; filename="{_safe_download_filename(filename)}"'
    )
    writer = csv.writer(response)
    writer.writerow(["Timestamp", "Event", "Actor", "Resource", "Identifier", "IP"])
    for log in queryset.iterator():
        writer.writerow(
            [
                _safe_csv_value(log.created_at.isoformat()),
                _safe_csv_value(log.get_event_type_display()),
                _safe_csv_value(DashboardDataProvider._actor_label(log)),
                _safe_csv_value(log.resource_type),
                _safe_csv_value(log.resource_identifier),
                _safe_csv_value(log.ip_address or ""),
            ]
        )
    return response
admin.site.index_title = "Dashboard"
admin.site.site_header = "Employer Access Portal"
admin.site.site_title = "Employer Access Portal"
