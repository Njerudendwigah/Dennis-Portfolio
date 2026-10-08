"""

Tests for the employer access portal.



The suite focuses on the security-sensitive workflow:

public request -> staff review -> temporary grant -> private resources -> audit log.

"""



from datetime import timedelta

from unittest.mock import patch



from django.contrib.auth import get_user_model

from django.core.exceptions import ValidationError

from django.core.files.uploadedfile import SimpleUploadedFile

from django.test import TestCase, override_settings

from django.urls import NoReverseMatch

from django.urls import reverse

from django.utils import timezone



from .forms import AccessRequestForm, StaffAuthenticationForm

from .models import (

    AccessGrant,

    AccessLog,

    AccessRequest,

    Document,

    DocumentAccessRequest,

    Employer,

    Referee,

    RefereeAccessRequest,

    validate_document_file,

)





from .views import grant_fingerprint


User = get_user_model()





class PortalTestMixin:

    """Shared test helpers for portal records and authenticated staff."""



    def reverse_first_available(self, names, **kwargs):

        """Reverse the first URL name that exists in the current project."""

        for name in names:

            try:

                return reverse(name, kwargs=kwargs)

            except NoReverseMatch:

                continue



        self.fail(

            "None of these URL names exist: " + ", ".join(names)

        )



    def create_staff(self, username="staff", password="StrongPass123!"):

        user = User.objects.create_user(

            username=username,

            password=password,

            is_staff=True,

        )

        return user, password



    def create_user(self, username="member", password="StrongPass123!"):

        user = User.objects.create_user(

            username=username,

            password=password,

            is_staff=False,

        )

        return user, password



    def create_resources(self):

        document = Document.objects.create(

            document_type=Document.DocumentType.CV,

            title="Current CV",

            description="Primary professional CV.",

        )

        referee = Referee.objects.create(

            name="Jane Doe",

            job_title="Operations Director",

            organisation="Example Logistics Ltd",

            email="jane@example.com",

            phone="+254700000000",

            relationship="Former Line Manager",

        )

        return document, referee



    def create_request(self, *, employer=None, status=None):

        employer = employer or Employer.objects.create(

            company_name="Example Logistics Ltd",

            contact_name="John Recruiter",

            job_title="Talent Partner",

            email="recruiter@example.com",

            phone="+254711111111",

        )

        access_request = AccessRequest.objects.create(

            employer=employer,

            requester_name="John Recruiter",

            requester_email=employer.email,

            requester_company=employer.company_name,

            requester_job_title=employer.job_title,

            requester_phone=employer.phone,

            reason=(

                "I am reviewing your professional experience for a suitable "

                "supply chain and operations opportunity."

            ),

            status=status or AccessRequest.Status.PENDING,

        )

        return access_request



    def attach_resources(self, access_request, document=None, referee=None):

        if document is not None:

            DocumentAccessRequest.objects.create(

                access_request=access_request,

                document=document,

            )

        if referee is not None:

            RefereeAccessRequest.objects.create(

                access_request=access_request,

                referee=referee,

            )



    def approve_request_directly(self, access_request, user=None, days=7):

        user = user or self.create_staff()[0]

        now = timezone.now()

        access_request.status = AccessRequest.Status.APPROVED

        access_request.reviewed_by = user

        access_request.reviewed_at = now

        access_request.approved_at = now

        access_request.expires_at = now + timedelta(days=days)

        access_request.save()



        DocumentAccessRequest.objects.filter(

            access_request=access_request,

        ).update(approved=True)

        RefereeAccessRequest.objects.filter(

            access_request=access_request,

        ).update(approved=True)



        return AccessGrant.objects.create(

            access_request=access_request,

            starts_at=now,

            expires_at=access_request.expires_at,

            is_active=True,

        )





class ModelAndFormTests(PortalTestMixin, TestCase):

    """Validate model properties and public request-form rules."""



    def test_currently_approved_property_requires_a_live_grant(self):

        access_request = self.create_request()

        access_request.status = AccessRequest.Status.APPROVED

        access_request.expires_at = timezone.now() + timedelta(hours=1)

        access_request.save(update_fields=["status", "expires_at", "updated_at"])



        # Approval without a corresponding grant is not enough to expose

        # private resources.

        self.assertFalse(access_request.is_currently_approved)



        now = timezone.now()

        grant = AccessGrant.objects.create(

            access_request=access_request,

            starts_at=now - timedelta(minutes=5),

            expires_at=now + timedelta(hours=1),

            is_active=True,

        )



        access_request.refresh_from_db()

        self.assertTrue(access_request.is_currently_approved)

        self.assertTrue(grant.is_currently_active)



        grant.expires_at = timezone.now() - timedelta(seconds=1)

        grant.save(update_fields=["expires_at"])



        access_request.refresh_from_db()

        self.assertFalse(access_request.is_currently_approved)



    def test_access_request_form_requires_at_least_one_resource(self):

        document, _referee = self.create_resources()



        form = AccessRequestForm(

            data={

                "requester_name": "John Recruiter",

                "requester_email": "recruiter@example.com",

                "requester_company": "Example Logistics Ltd",

                "requester_job_title": "Talent Partner",

                "requester_phone": "+254711111111",

                "reason": (

                    "I am reviewing your professional experience for a suitable "

                    "supply chain and operations opportunity."

                ),

                "requested_documents": [],

                "requested_referees": [],

            }

        )



        self.assertFalse(form.is_valid())

        self.assertIn(

            "Please select at least one document or referee.",

            form.non_field_errors(),

        )

        self.assertTrue(Document.objects.filter(pk=document.pk).exists())



    def test_access_request_form_creates_employer_and_permission_rows(self):

        document, referee = self.create_resources()



        form = AccessRequestForm(

            data={

                "requester_name": "John Recruiter",

                "requester_email": "Recruiter@Example.com",

                "requester_company": "Example Logistics Ltd",

                "requester_job_title": "Talent Partner",

                "requester_phone": "+254711111111",

                "reason": (

                    "I am reviewing your professional experience for a suitable "

                    "supply chain and operations opportunity."

                ),

                "requested_documents": [document.pk],

                "requested_referees": [referee.pk],

            }

        )



        self.assertTrue(form.is_valid(), form.errors)

        access_request = form.save()



        self.assertIsNotNone(access_request.employer)

        self.assertEqual(

            access_request.employer.email,

            "recruiter@example.com",

        )

        self.assertTrue(

            DocumentAccessRequest.objects.filter(

                access_request=access_request,

                document=document,

                approved=False,

            ).exists()

        )

        self.assertTrue(

            RefereeAccessRequest.objects.filter(

                access_request=access_request,

                referee=referee,

                approved=False,

            ).exists()

        )





class AuthenticationAndRequestFlowTests(PortalTestMixin, TestCase):

    """Verify public submission and staff-only authentication."""



    def test_staff_authentication_form_rejects_non_staff_users(self):

        user, password = self.create_user()



        form = StaffAuthenticationForm(

            request=None,

            data={

                "username": user.username,

                "password": password,

            },

        )



        self.assertFalse(form.is_valid())

        self.assertIn(

            "This account does not have staff access.",

            form.non_field_errors(),

        )



    def test_request_access_page_loads(self):

        document, referee = self.create_resources()



        response = self.client.get(reverse("employer_portal:request_access"))



        self.assertEqual(response.status_code, 200)

        self.assertContains(response, document.title)

        self.assertContains(response, referee.name)



    @override_settings(EMPLOYER_NOTIFICATION_EMAIL="")

    def test_request_access_creates_request_and_audit_log(self):

        document, referee = self.create_resources()



        response = self.client.post(

            reverse("employer_portal:request_access"),

            data={

                "requester_name": "John Recruiter",

                "requester_email": "Recruiter@Example.com",

                "requester_company": "Example Logistics Ltd",

                "requester_job_title": "Talent Partner",

                "requester_phone": "+254711111111",

                "reason": (

                    "I am reviewing your professional experience for a suitable "

                    "supply chain and operations opportunity."

                ),

                "requested_documents": [document.pk],

                "requested_referees": [referee.pk],

            },

            REMOTE_ADDR="192.0.2.25",

            HTTP_USER_AGENT="PortalTest/1.0",

        )



        access_request = AccessRequest.objects.get(

            requester_email="recruiter@example.com",

        )



        self.assertRedirects(

            response,

            reverse(

                "employer_portal:request_submitted",

                kwargs={"request_id": access_request.request_id},

            ),

        )

        self.assertEqual(access_request.employer.email, "recruiter@example.com")

        self.assertEqual(access_request.ip_address, "192.0.2.25")

        self.assertEqual(access_request.user_agent, "PortalTest/1.0")



        audit = AccessLog.objects.get(

            access_request=access_request,

            event_type=AccessLog.EventType.REQUEST_SUBMITTED,

        )

        self.assertEqual(audit.resource_type, "access_request")

        self.assertEqual(audit.resource_identifier, str(access_request.request_id))



    def test_anonymous_user_is_redirected_from_staff_dashboard(self):

        response = self.client.get(reverse("employer_portal:staff_dashboard"))



        self.assertEqual(response.status_code, 302)

        self.assertIn(

            reverse("employer_portal:login"),

            response["Location"],

        )



    def test_authenticated_non_staff_user_gets_forbidden_staff_dashboard(self):

        user, _password = self.create_user()

        self.client.force_login(user)



        response = self.client.get(reverse("employer_portal:staff_dashboard"))



        self.assertEqual(response.status_code, 403)



    def test_staff_user_can_open_staff_dashboard(self):

        user, _password = self.create_staff()

        self.client.force_login(user)



        response = self.client.get(reverse("employer_portal:staff_dashboard"))



        self.assertEqual(response.status_code, 200)

        self.assertContains(response, "Employer access")





class GrantLifecycleTests(PortalTestMixin, TestCase):

    """Verify approval, revocation and expiry rules."""



    @patch("employer_portal.views.send_mail")

    def test_staff_can_approve_pending_request(self, mocked_send_mail):

        user, _password = self.create_staff()

        document, referee = self.create_resources()

        access_request = self.create_request()

        self.attach_resources(access_request, document=document, referee=referee)



        self.client.force_login(user)

        response = self.client.post(

            reverse(

                "employer_portal:approve_request",

                kwargs={"request_id": access_request.request_id},

            )

        )



        access_request.refresh_from_db()

        grant = AccessGrant.objects.get(access_request=access_request)



        self.assertRedirects(

            response,

            reverse(

                "employer_portal:staff_request_detail",

                kwargs={"request_id": access_request.request_id},

            ),

        )

        self.assertEqual(access_request.status, AccessRequest.Status.APPROVED)

        self.assertTrue(grant.is_active)

        self.assertGreater(

            grant.expires_at,

            grant.starts_at + timedelta(days=6),

        )

        self.assertLess(

            grant.expires_at,

            grant.starts_at + timedelta(days=8),

        )

        self.assertTrue(

            DocumentAccessRequest.objects.get(

                access_request=access_request,

                document=document,

            ).approved

        )

        self.assertTrue(

            RefereeAccessRequest.objects.get(

                access_request=access_request,

                referee=referee,

            ).approved

        )

        self.assertTrue(

            AccessLog.objects.filter(

                access_request=access_request,

                event_type=AccessLog.EventType.REQUEST_APPROVED,

            ).exists()

        )

        mocked_send_mail.assert_called_once()



    @patch("employer_portal.views.send_mail")

    def test_non_pending_request_cannot_be_approved_again(self, mocked_send_mail):

        user, _password = self.create_staff()

        access_request = self.create_request(status=AccessRequest.Status.REJECTED)



        self.client.force_login(user)

        response = self.client.post(

            reverse(

                "employer_portal:approve_request",

                kwargs={"request_id": access_request.request_id},

            )

        )



        access_request.refresh_from_db()



        self.assertEqual(response.status_code, 302)

        self.assertEqual(access_request.status, AccessRequest.Status.REJECTED)

        mocked_send_mail.assert_not_called()



    def test_staff_can_reject_pending_request(self):

        user, _password = self.create_staff()

        access_request = self.create_request()



        self.client.force_login(user)

        response = self.client.post(

            reverse(

                "employer_portal:reject_request",

                kwargs={"request_id": access_request.request_id},

            )

        )



        access_request.refresh_from_db()



        self.assertRedirects(

            response,

            reverse(

                "employer_portal:staff_request_detail",

                kwargs={"request_id": access_request.request_id},

            ),

        )

        self.assertEqual(access_request.status, AccessRequest.Status.REJECTED)

        self.assertTrue(

            AccessLog.objects.filter(

                access_request=access_request,

                event_type=AccessLog.EventType.REQUEST_REJECTED,

            ).exists()

        )



    def test_staff_can_revoke_active_request(self):

        user, _password = self.create_staff()

        access_request = self.create_request(

            status=AccessRequest.Status.APPROVED,

        )

        grant = self.approve_request_directly(access_request, user=user)



        self.client.force_login(user)

        revoke_url = self.reverse_first_available(

            (

                "employer_portal:revoke_request",

                "employer_portal:revoke_access",

                "employer_portal:revoke",

            ),

            request_id=access_request.request_id,

        )



        response = self.client.post(revoke_url)



        access_request.refresh_from_db()

        grant.refresh_from_db()



        self.assertRedirects(

            response,

            reverse(

                "employer_portal:staff_request_detail",

                kwargs={"request_id": access_request.request_id},

            ),

        )

        self.assertEqual(access_request.status, AccessRequest.Status.REVOKED)

        self.assertFalse(grant.is_active)

        self.assertIsNotNone(grant.revoked_at)

        self.assertTrue(

            AccessLog.objects.filter(

                access_request=access_request,

                event_type=AccessLog.EventType.ACCESS_REVOKED,

            ).exists()

        )



    def test_expired_grant_is_denied_and_request_marked_expired(self):

        access_request = self.create_request(

            status=AccessRequest.Status.APPROVED,

        )

        now = timezone.now()

        grant = AccessGrant.objects.create(

            access_request=access_request,

            starts_at=now - timedelta(days=2),

            expires_at=now - timedelta(hours=1),

            is_active=True,

        )

        access_request.expires_at = grant.expires_at

        access_request.save(update_fields=["expires_at", "updated_at"])



        response = self.client.get(

            reverse(

                "employer_portal:portal",

                kwargs={"token": grant.token},

            )

        )



        self.assertEqual(response.status_code, 404)



        grant.refresh_from_db()

        access_request.refresh_from_db()

        self.assertFalse(grant.is_active)

        self.assertEqual(access_request.status, AccessRequest.Status.EXPIRED)





class PrivateResourceAccessTests(PortalTestMixin, TestCase):

    """Verify token-gated private documents and referee records."""



    def create_file_document(self, title, filename, content=b"private content"):

        document = Document.objects.create(

            document_type=Document.DocumentType.CV,

            title=title,

            file=SimpleUploadedFile(

                filename,

                content,

                content_type="text/plain",

            ),

        )

        self.addCleanup(self._cleanup_document_file, document)

        return document



    @staticmethod

    def _cleanup_document_file(document):

        try:

            if document.file:

                document.file.delete(save=False)

        except Exception:

            pass



    def test_portal_shows_only_approved_active_resources(self):

        document = self.create_file_document(

            "Approved CV",

            "approved-cv.txt",

        )

        hidden_document = self.create_file_document(

            "Hidden CV",

            "hidden-cv.txt",

        )

        referee = Referee.objects.create(

            name="Jane Doe",

            job_title="Operations Director",

            organisation="Example Logistics Ltd",

        )



        access_request = self.create_request(

            status=AccessRequest.Status.APPROVED,

        )

        now = timezone.now()

        grant = AccessGrant.objects.create(

            access_request=access_request,

            starts_at=now,

            expires_at=now + timedelta(days=7),

            is_active=True,

        )



        DocumentAccessRequest.objects.create(

            access_request=access_request,

            document=document,

            approved=True,

        )

        DocumentAccessRequest.objects.create(

            access_request=access_request,

            document=hidden_document,

            approved=False,

        )

        RefereeAccessRequest.objects.create(

            access_request=access_request,

            referee=referee,

            approved=True,

        )



        response = self.client.get(

            reverse(

                "employer_portal:portal",

                kwargs={"token": grant.token},

            )

        )



        self.assertEqual(response.status_code, 200)

        self.assertContains(response, document.title)

        self.assertContains(response, referee.name)

        self.assertNotContains(response, hidden_document.title)

        self.assertEqual(

            response["Cache-Control"],

            "private, no-store, max-age=0",

        )



    def test_approved_document_download_is_logged(self):

        document = self.create_file_document(

            "Current CV",

            "current-cv.txt",

            content=b"Dennis Ndwigah CV",

        )

        access_request = self.create_request(

            status=AccessRequest.Status.APPROVED,

        )

        now = timezone.now()

        grant = AccessGrant.objects.create(

            access_request=access_request,

            starts_at=now,

            expires_at=now + timedelta(days=7),

            is_active=True,

        )

        item = DocumentAccessRequest.objects.create(

            access_request=access_request,

            document=document,

            approved=True,

        )



        response = self.client.get(

            reverse(

                "employer_portal:document_download",

                kwargs={

                    "token": grant.token,

                    "document_id": document.id,

                },

            ),

        )



        self.assertEqual(response.status_code, 200)

        disposition = response["Content-Disposition"]

        self.assertTrue(

            disposition.startswith('attachment; filename="')

        )

        self.assertTrue(

            disposition.endswith('.txt"')

        )



        item.refresh_from_db()

        self.assertIsNotNone(item.viewed_at)

        self.assertTrue(

            AccessLog.objects.filter(

                access_request=access_request,

                event_type=AccessLog.EventType.DOCUMENT_DOWNLOADED,

                resource_identifier=str(document.id),

            ).exists()

        )



    def test_unapproved_document_cannot_be_downloaded(self):

        document = self.create_file_document(

            "Restricted CV",

            "restricted-cv.txt",

        )

        access_request = self.create_request(

            status=AccessRequest.Status.APPROVED,

        )

        now = timezone.now()

        grant = AccessGrant.objects.create(

            access_request=access_request,

            starts_at=now,

            expires_at=now + timedelta(days=7),

            is_active=True,

        )

        DocumentAccessRequest.objects.create(

            access_request=access_request,

            document=document,

            approved=False,

        )



        response = self.client.get(

            reverse(

                "employer_portal:document_download",

                kwargs={

                    "token": grant.token,

                    "document_id": document.id,

                },

            ),

        )



        self.assertEqual(response.status_code, 404)



    def test_referee_view_is_logged(self):

        referee = Referee.objects.create(

            name="Jane Doe",

            job_title="Operations Director",

            organisation="Example Logistics Ltd",

            email="jane@example.com",

        )

        access_request = self.create_request(

            status=AccessRequest.Status.APPROVED,

        )

        now = timezone.now()

        grant = AccessGrant.objects.create(

            access_request=access_request,

            starts_at=now,

            expires_at=now + timedelta(days=7),

            is_active=True,

        )

        item = RefereeAccessRequest.objects.create(

            access_request=access_request,

            referee=referee,

            approved=True,

        )



        referee_url = self.reverse_first_available(

            (

                "employer_portal:referee_view",

                "employer_portal:referee",

            ),

            token=grant.token,

            referee_id=referee.id,

        )



        response = self.client.get(referee_url)



        self.assertEqual(response.status_code, 200)

        self.assertContains(response, referee.name)



        item.refresh_from_db()

        self.assertIsNotNone(item.viewed_at)

        self.assertTrue(

            AccessLog.objects.filter(

                access_request=access_request,

                event_type=AccessLog.EventType.REFEREE_VIEWED,

                resource_identifier=str(referee.id),

            ).exists()

        )





class RequestStatusTests(PortalTestMixin, TestCase):

    """Verify the status page reflects expired grants."""



    def test_request_status_expires_stale_grant(self):

        access_request = self.create_request(

            status=AccessRequest.Status.APPROVED,

        )



        now = timezone.now()

        grant = AccessGrant.objects.create(

            access_request=access_request,

            starts_at=now - timedelta(days=2),

            expires_at=now - timedelta(minutes=5),

            is_active=True,

        )



        access_request.expires_at = grant.expires_at

        access_request.save(update_fields=["expires_at", "updated_at"])



        response = self.client.get(

            reverse(

                "employer_portal:request_status",

                kwargs={"request_id": access_request.request_id},

            )

        )



        self.assertEqual(response.status_code, 200)



        grant.refresh_from_db()

        access_request.refresh_from_db()



        self.assertFalse(grant.is_active)

        self.assertEqual(access_request.status, AccessRequest.Status.EXPIRED)

        self.assertContains(response, access_request.requester_name)


class SecurityHardeningTests(PortalTestMixin, TestCase):
    """Regression tests for private-document and grant-token security."""

    def test_unsupported_document_extension_is_rejected(self):
        upload = SimpleUploadedFile(
            "malicious.exe",
            b"not an executable",
            content_type="application/octet-stream",
        )

        with self.assertRaises(ValidationError):
            validate_document_file(upload)

    def test_supported_document_extension_is_accepted(self):
        upload = SimpleUploadedFile(
            "professional-cv.pdf",
            b"%PDF-test",
            content_type="application/pdf",
        )

        validate_document_file(upload)

    def test_grant_fingerprint_is_stable_and_not_the_raw_token(self):
        access_request = self.create_request()
        grant = self.approve_request_directly(access_request)

        fingerprint = grant_fingerprint(grant.token)

        self.assertEqual(fingerprint, grant_fingerprint(grant.token))
        self.assertEqual(len(fingerprint), 16)
        self.assertNotEqual(fingerprint, str(grant.token))
        self.assertNotIn(str(grant.token), fingerprint)

    def test_portal_audit_log_does_not_store_raw_grant_token(self):
        access_request = self.create_request(status=AccessRequest.Status.APPROVED)
        grant = self.approve_request_directly(access_request)

        response = self.client.get(
            reverse(
                "employer_portal:portal",
                kwargs={"token": grant.token},
            )
        )

        self.assertEqual(response.status_code, 200)

        audit = AccessLog.objects.get(
            access_request=access_request,
            event_type=AccessLog.EventType.PORTAL_VIEWED,
        )

        self.assertNotIn("grant_token", audit.metadata)
        self.assertNotIn(str(grant.token), str(audit.metadata))

    def test_document_download_audit_does_not_store_raw_grant_token(self):
        document = Document.objects.create(
            document_type=Document.DocumentType.CV,
            title="Security Test CV",
            file=SimpleUploadedFile(
                "security-test.txt",
                b"security test content",
                content_type="text/plain",
            ),
        )
        self.addCleanup(document.file.delete, save=False)
        access_request = self.create_request(
            status=AccessRequest.Status.APPROVED,
        )
        grant = self.approve_request_directly(access_request)

        DocumentAccessRequest.objects.create(
            access_request=access_request,
            document=document,
            approved=True,
        )

        response = self.client.get(
            reverse(
                "employer_portal:document_download",
                kwargs={
                    "token": grant.token,
                    "document_id": document.id,
                },
            )
        )

        self.assertEqual(response.status_code, 200)

        audit = AccessLog.objects.get(
            access_request=access_request,
            event_type=AccessLog.EventType.DOCUMENT_DOWNLOADED,
        )

        self.assertNotIn("grant_token", audit.metadata)
        self.assertNotIn(str(grant.token), str(audit.metadata))

        # Close the file-backed response before Django test cleanup runs.
        # This prevents Windows from locking the uploaded document.
        response.close()

