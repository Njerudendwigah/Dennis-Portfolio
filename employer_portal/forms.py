"""

Forms for the Dennis Ndwigah employer access portal.



The public access-request form collects employer identity, the reason for

the request, and the specific professional documents/referees being

requested. Only active resources are selectable.



Staff authentication is deliberately restricted to Django staff accounts.

"""



from __future__ import annotations



from django import forms

from django.contrib.auth.forms import AuthenticationForm

from django.core.exceptions import ValidationError

from django.db import transaction



from .models import (

    AccessRequest,

    Document,

    DocumentAccessRequest,

    Employer,

    Referee,

    RefereeAccessRequest,

)





MIN_REASON_LENGTH = 20

MAX_REASON_LENGTH = 5000

MAX_EMAIL_LENGTH = 254





# ---------------------------------------------------------------------------

# SHARED NORMALISERS

# ---------------------------------------------------------------------------





def _normalise_email(value: str) -> str:

    """Lowercase and strip an email address for consistent lookups."""

    return (value or "").strip().lower()





def _normalise_text(value: str, *, max_length: int | None = None) -> str:

    """Strip leading/trailing whitespace and collapse internal runs."""

    cleaned = " ".join((value or "").split())

    if max_length is not None:

        cleaned = cleaned[:max_length]

    return cleaned





# ---------------------------------------------------------------------------

# STAFF AUTHENTICATION

# ---------------------------------------------------------------------------





class StaffAuthenticationForm(AuthenticationForm):

    """

    Authentication form restricted to active Django staff accounts.



    Non-staff users get a form-level error rather than a redirect to the

    admin login. Inactive staff accounts are rejected before the password

    check, matching Django's built-in behaviour.

    """



    error_messages = {

        **AuthenticationForm.error_messages,

        "not_staff": "This account does not have staff access.",

        "inactive": "This staff account has been deactivated.",

    }



    def confirm_login_allowed(self, user) -> None:

        super().confirm_login_allowed(user)



        if not user.is_active:

            raise ValidationError(

                self.error_messages["inactive"],

                code="inactive",

            )



        if not user.is_staff:

            raise ValidationError(

                self.error_messages["not_staff"],

                code="staff_required",

            )





# ---------------------------------------------------------------------------

# PUBLIC ACCESS REQUEST

# ---------------------------------------------------------------------------





class AccessRequestForm(forms.ModelForm):

    """

    Public employer request form for private portfolio access.



    Only active documents and referees appear in the selectors, so a

    malformed POST cannot grant access to a resource that has since been

    deactivated.

    """



    requested_documents = forms.ModelMultipleChoiceField(

        label="Documents requested",

        queryset=Document.objects.none(),

        required=False,

        widget=forms.CheckboxSelectMultiple,

        help_text="Select the professional documents you need to review.",

        error_messages={

            "invalid_choice": "One of the selected documents is not available.",

        },

    )



    requested_referees = forms.ModelMultipleChoiceField(

        label="Referees requested",

        queryset=Referee.objects.none(),

        required=False,

        widget=forms.CheckboxSelectMultiple,

        help_text="Select referees you are requesting permission to contact.",

        error_messages={

            "invalid_choice": "One of the selected referees is not available.",

        },

    )



    class Meta:

        model = AccessRequest

        fields = [

            "requester_name",

            "requester_email",

            "requester_company",

            "requester_job_title",

            "requester_phone",

            "reason",

        ]

        widgets = {

            "requester_name": forms.TextInput(

                attrs={

                    "autocomplete": "name",

                    "maxlength": 150,

                    "required": True,

                }

            ),

            "requester_email": forms.EmailInput(

                attrs={

                    "autocomplete": "email",

                    "inputmode": "email",

                    "maxlength": MAX_EMAIL_LENGTH,

                    "required": True,

                }

            ),

            "requester_company": forms.TextInput(

                attrs={

                    "autocomplete": "organization",

                    "maxlength": 200,

                    "required": True,

                }

            ),

            "requester_job_title": forms.TextInput(

                attrs={

                    "autocomplete": "organization-title",

                    "maxlength": 150,

                }

            ),

            "requester_phone": forms.TextInput(

                attrs={

                    "autocomplete": "tel",

                    "inputmode": "tel",

                    "maxlength": 40,

                }

            ),

            "reason": forms.Textarea(

                attrs={

                    "rows": 3,

                    "maxlength": MAX_REASON_LENGTH,

                    "minlength": MIN_REASON_LENGTH,

                    "required": True,

                    "placeholder": (

                        "Please explain the role or hiring process and why "

                        "you need access to these materials."

                    ),

                }

            ),

        }



    # ------------------------------------------------------------------

    # SETUP

    # ------------------------------------------------------------------

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)



        # Only active resources are selectable. Deactivating a document

        # between page load and submit is caught by the field validator.

        self.fields["requested_documents"].queryset = (

            Document.objects.active().order_by("document_type", "title")

        )

        self.fields["requested_referees"].queryset = (

            Referee.objects.filter(is_active=True).order_by("name")

        )



    # ------------------------------------------------------------------

    # FIELD CLEANING

    # ------------------------------------------------------------------

    def clean_requester_name(self) -> str:

        value = _normalise_text(self.cleaned_data.get("requester_name", ""))

        if len(value) < 2:

            raise ValidationError("Please enter your full name.")

        return value



    def clean_requester_email(self) -> str:

        value = _normalise_email(self.cleaned_data.get("requester_email", ""))

        if not value:

            raise ValidationError("Please enter your email address.")

        return value



    def clean_requester_company(self) -> str:

        value = _normalise_text(self.cleaned_data.get("requester_company", ""))

        if len(value) < 2:

            raise ValidationError(

                "Please enter your company or organisation name."

            )

        return value



    def clean_requester_job_title(self) -> str:

        return _normalise_text(self.cleaned_data.get("requester_job_title", ""))



    def clean_requester_phone(self) -> str:

        return _normalise_text(self.cleaned_data.get("requester_phone", ""))



    def clean_reason(self) -> str:

        value = (self.cleaned_data.get("reason") or "").strip()

        if len(value) < MIN_REASON_LENGTH:

            raise ValidationError(

                "Please provide a little more detail about your access request."

            )

        if len(value) > MAX_REASON_LENGTH:

            raise ValidationError(

                f"Please keep your reason under {MAX_REASON_LENGTH} characters."

            )

        return value



    # ------------------------------------------------------------------

    # CROSS-FIELD VALIDATION

    # ------------------------------------------------------------------

    def clean(self):

        cleaned_data = super().clean()



        documents = cleaned_data.get("requested_documents")

        referees = cleaned_data.get("requested_referees")



        if not documents and not referees:
            raise ValidationError(
                "Please select at least one document or referee."
            )

        return cleaned_data



    # ------------------------------------------------------------------

    # PERSISTENCE

    # ------------------------------------------------------------------

    def save(self, commit: bool = True) -> AccessRequest:

        """

        Save the access request and create its requested-resource records.



        The related Employer record is reused when both email and company

        already identify the same employer, otherwise a new Employer record

        is created. The access request keeps a snapshot of the submitted

        requester information independently of that employer record.



        With ``commit=False`` the instance is returned un-saved and no

        employer reconciliation or through-table rows are created; the

        caller is responsible for both.

        """

        access_request = super().save(commit=False)



        # ``_post_clean`` already assigned the cleaned values onto the

        # instance, but re-apply the normalised snapshot here so that

        # ``commit=False`` callers get a fully populated object even if

        # they mutate ``cleaned_data`` downstream.

        self._apply_snapshot(access_request)



        if not commit:

            return access_request



        with transaction.atomic():

            employer = self._resolve_employer(access_request)

            access_request.employer = employer

            access_request.save()

            self.save_requested_resources(access_request)



        return access_request



    def save_m2m(self) -> None:  # pragma: no cover - reserved

        """

        Django's ``ModelForm`` protocol calls this after ``save(commit=True)``

        when ``save_m2m`` is defined. Through-table creation is handled

        inside ``save_requested_resources`` instead, so this is a no-op.

        """

        pass



    def save_requested_resources(

        self,

        access_request: AccessRequest,

    ) -> None:

        """

        Replace the through-table records for the requested resources.



        Uses ``ignore_conflicts=True`` so a duplicate choice (which the

        field validator already rejects) cannot abort the transaction

        with an ``IntegrityError`` at the database level.

        """

        documents = list(self.cleaned_data.get("requested_documents") or [])

        referees = list(self.cleaned_data.get("requested_referees") or [])



        DocumentAccessRequest.objects.filter(

            access_request=access_request,

        ).delete()

        RefereeAccessRequest.objects.filter(

            access_request=access_request,

        ).delete()



        if documents:

            DocumentAccessRequest.objects.bulk_create(

                [

                    DocumentAccessRequest(

                        access_request=access_request,

                        document=document,

                        approved=False,

                    )

                    for document in documents

                ],

                ignore_conflicts=True,

            )



        if referees:

            RefereeAccessRequest.objects.bulk_create(

                [

                    RefereeAccessRequest(

                        access_request=access_request,

                        referee=referee,

                        approved=False,

                    )

                    for referee in referees

                ],

                ignore_conflicts=True,

            )



    # ------------------------------------------------------------------

    # INTERNAL HELPERS

    # ------------------------------------------------------------------

    @staticmethod

    def _apply_snapshot(access_request: AccessRequest) -> None:

        """Copy the normalised requester snapshot onto the instance."""

        data = access_request  # readability alias

        # Values are already normalised by the ``clean_*`` methods, so

        # this is a defensive no-op for callers that bypass validation.

        data.requester_name = _normalise_text(data.requester_name or "")

        data.requester_email = _normalise_email(data.requester_email or "")

        data.requester_company = _normalise_text(data.requester_company or "")

        data.requester_job_title = _normalise_text(data.requester_job_title or "")

        data.requester_phone = _normalise_text(data.requester_phone or "")

        data.reason = (data.reason or "").strip()



    @staticmethod

    def _resolve_employer(access_request: AccessRequest) -> Employer:

        """

        Find or create the ``Employer`` matching the requester snapshot.



        Matching is case-insensitive on both email and company name so

        repeat requesters reuse the same employer record. When a match is

        found, blank or stale contact fields are refreshed in place.

        """

        employer = (

            Employer.objects

            .filter(

                email__iexact=access_request.requester_email,

                company_name__iexact=access_request.requester_company,

            )

            .order_by("-created_at")

            .first()

        )



        if employer is None:

            return Employer.objects.create(

                company_name=access_request.requester_company,

                email=access_request.requester_email,

                contact_name=access_request.requester_name,

                job_title=access_request.requester_job_title,

                phone=access_request.requester_phone,

                is_active=True,

            )



        changed = []



        if employer.contact_name != access_request.requester_name:

            employer.contact_name = access_request.requester_name

            changed.append("contact_name")



        if employer.job_title != access_request.requester_job_title:

            employer.job_title = access_request.requester_job_title

            changed.append("job_title")



        if employer.phone != access_request.requester_phone:

            employer.phone = access_request.requester_phone

            changed.append("phone")



        if changed:

            changed.append("updated_at")

            employer.save(update_fields=changed)



        return employer