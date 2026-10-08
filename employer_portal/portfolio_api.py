from __future__ import annotations

import hashlib
import json
import secrets
from datetime import timedelta
from functools import wraps

from django.conf import settings
from django.contrib.auth import authenticate, get_user_model
from django.core import signing
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from .portfolio_models import PortfolioContent, PortfolioSession


ALLOWED_KEYS = frozenset(
    {
        "portfolioProfile",
        "portfolioExperience",
        "dennis_projects",
        "dennis_skills",
        "dennis_certifications",
        "portfolioSettings",
    }
)

MAX_PORTFOLIO_PAYLOAD_BYTES = 1_000_000
TOKEN_SALT = "portfolio-api"


def _cors_headers(request):
    origin = request.headers.get("Origin", "")
    allowed = getattr(
        settings,
        "PORTFOLIO_ADMIN_ORIGIN",
        "",
    ).rstrip("/")

    if not origin or origin.rstrip("/") != allowed:
        return {}

    return {
        "Access-Control-Allow-Origin": origin,
        "Access-Control-Allow-Headers": "Authorization, Content-Type",
        "Access-Control-Allow-Methods": "GET, POST, PUT, OPTIONS",
        "Vary": "Origin",
    }


def _json_response(request, data, status=200):
    response = JsonResponse(
        data,
        status=status,
        json_dumps_params={"ensure_ascii": False},
    )

    for name, value in _cors_headers(request).items():
        response[name] = value

    response["Cache-Control"] = "no-store"
    response["Pragma"] = "no-cache"

    return response


def _token_hash(token):
    return hashlib.sha256(
        token.encode("utf-8")
    ).hexdigest()


def _token_for_user(user):
    session_id = secrets.token_urlsafe(32)

    payload = json.dumps(
        {
            "user_id": user.pk,
            "username": user.get_username(),
            "session_id": session_id,
        }
    )

    token = signing.TimestampSigner(
        salt=TOKEN_SALT
    ).sign(payload)

    expires_at = timezone.now() + timedelta(
        seconds=settings.PORTFOLIO_API_TOKEN_MAX_AGE
    )

    PortfolioSession.objects.create(
        session_id=session_id,
        user=user,
        token_hash=_token_hash(token),
        expires_at=expires_at,
    )

    return token


def _user_from_token(request):
    authorization = request.headers.get(
        "Authorization",
        "",
    )

    if not authorization.startswith("Bearer "):
        return None

    token = authorization[7:].strip()

    if not token:
        return None

    try:
        payload = signing.TimestampSigner(
            salt=TOKEN_SALT
        ).unsign(
            token,
            max_age=settings.PORTFOLIO_API_TOKEN_MAX_AGE,
        )

        data = json.loads(payload)

        user_id = int(data["user_id"])
        session_id = str(data["session_id"])
        username = str(data["username"])

    except (
        ValueError,
        TypeError,
        KeyError,
        json.JSONDecodeError,
        signing.BadSignature,
    ):
        return None

    session = (
        PortfolioSession.objects
        .select_related("user")
        .filter(
            session_id=session_id,
            token_hash=_token_hash(token),
            revoked_at__isnull=True,
            expires_at__gt=timezone.now(),
            user_id=user_id,
        )
        .first()
    )

    if session is None:
        return None

    user = session.user

    if not user.is_active or not user.is_staff:
        return None

    if username != user.get_username():
        return None

    return user


def _revoke_token(request):
    authorization = request.headers.get(
        "Authorization",
        "",
    )

    if not authorization.startswith("Bearer "):
        return

    token = authorization[7:].strip()

    if not token:
        return

    PortfolioSession.objects.filter(
        token_hash=_token_hash(token),
        revoked_at__isnull=True,
    ).update(
        revoked_at=timezone.now()
    )


def staff_api_required(view_func):
    @wraps(view_func)
    def wrapped(request, *args, **kwargs):
        if request.method == "OPTIONS":
            return _json_response(
                request,
                {"ok": True},
            )

        user = _user_from_token(request)

        if user is None:
            return _json_response(
                request,
                {"detail": "Authentication required."},
                status=401,
            )

        request.portfolio_user = user

        return view_func(
            request,
            *args,
            **kwargs,
        )

    return wrapped


@require_http_methods(["OPTIONS", "POST"])
def login(request):
    if request.method == "OPTIONS":
        return _json_response(
            request,
            {"ok": True},
        )

    try:
        body = json.loads(
            request.body or "{}"
        )
    except json.JSONDecodeError:
        return _json_response(
            request,
            {"detail": "Invalid JSON."},
            status=400,
        )

    email = str(
        body.get("email", "")
    ).strip()

    password = str(
        body.get("password", "")
    )

    if not email or not password:
        return _json_response(
            request,
            {
                "detail": (
                    "Email and password are required."
                )
            },
            status=400,
        )

    user = authenticate(
        request,
        username=email,
        password=password,
    )

    if user is None:
        candidate = (
            get_user_model()
            .objects
            .filter(email__iexact=email)
            .first()
        )

        if candidate is not None:
            user = authenticate(
                request,
                username=candidate.get_username(),
                password=password,
            )

    if (
        user is None
        or not user.is_active
        or not user.is_staff
    ):
        return _json_response(
            request,
            {"detail": "Invalid staff credentials."},
            status=401,
        )

    token = _token_for_user(user)

    return _json_response(
        request,
        {
            "authenticated": True,
            "token": token,
            "expiresIn": settings.PORTFOLIO_API_TOKEN_MAX_AGE,
            "user": {
                "username": user.get_username(),
                "email": user.email,
            },
        },
    )


@require_http_methods(["OPTIONS", "POST"])
def logout(request):
    if request.method == "OPTIONS":
        return _json_response(
            request,
            {"ok": True},
        )

    _revoke_token(request)

    return _json_response(
        request,
        {"authenticated": False},
    )


@require_http_methods(["OPTIONS", "GET"])
@staff_api_required
def data(request):
    records = PortfolioContent.objects.filter(
        key__in=ALLOWED_KEYS
    )

    sections = {
        record.key: record.data
        for record in records
    }

    return _json_response(
        request,
        {
            "sections": sections,
            "keys": sorted(ALLOWED_KEYS),
        },
    )


@require_http_methods(["OPTIONS", "PUT"])
@staff_api_required
def section(request, key):
    if key not in ALLOWED_KEYS:
        return _json_response(
            request,
            {"detail": "Unknown portfolio section."},
            status=404,
        )

    if len(request.body) > MAX_PORTFOLIO_PAYLOAD_BYTES:
        return _json_response(
            request,
            {"detail": "Portfolio payload is too large."},
            status=413,
        )

    try:
        body = json.loads(
            request.body or "{}"
        )
    except json.JSONDecodeError:
        return _json_response(
            request,
            {"detail": "Invalid JSON."},
            status=400,
        )

    if not isinstance(body, (dict, list)):
        return _json_response(
            request,
            {
                "detail": (
                    "Portfolio data must be a JSON "
                    "object or array."
                )
            },
            status=400,
        )

    record, _ = PortfolioContent.objects.get_or_create(
        key=key,
        defaults={"data": {}},
    )

    record.data = body
    record.updated_by = request.portfolio_user

    record.save(
        update_fields=[
            "data",
            "updated_by",
            "updated_at",
        ]
    )

    return _json_response(
        request,
        {
            "key": record.key,
            "data": record.data,
        },
    )