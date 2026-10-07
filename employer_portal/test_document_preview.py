"""
Tests for the secure employer document preview flow.

The tests cover the preview page, protected document streaming, and the
access controls that protect both endpoints.
"""

from datetime import timedelta

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import (
    AccessGrant,
    AccessLog,
    AccessRequest,
    Document,
    DocumentAccessRequest,
    Employer,
)


class DocumentPreviewTests(TestCase):
    """Verify secure document preview and streaming behaviour."""

    def create_document(
        self,
        filename="current-cv.pdf",
        content=b"PDF test content",
    ):
        document = Document.objects.create(
            document_type=Document.DocumentType.CV,
            title="Current CV",
            description="Primary professional CV.",
            file=SimpleUploadedFile(
                filename,
                content,
                content_type="application/pdf",
            ),
        )
        self.addCleanup(self.delete_document_file, document)
        return document

    @staticmethod
    def delete_document_file(document):
        try:
            if document.file:
                document.file.delete(save=False)
        except Exception:
            pass

    def create_grant(self, document):
        employer = Employer.objects.create(
            company_name="Example Logistics Ltd",
            contact_name="John Recruiter",
            job_title="Talent Partner",
            email="recruiter@example.com",
            phone="+254711111111",
        )

        now = timezone.now()

        access_request = AccessRequest.objects.create(
            employer=employer,
            requester_name="John Recruiter",
            requester_email=employer.email,
            requester_company=employer.company_name,
            requester_job_title=employer.job_title,
            requester_phone=employer.phone,
            reason="Reviewing professional experience for a suitable opportunity.",
            status=AccessRequest.Status.APPROVED,
            reviewed_at=now,
            approved_at=now,
            expires_at=now + timedelta(days=7),
        )

        DocumentAccessRequest.objects.create(
            access_request=access_request,
            document=document,
            approved=True,
        )

        return AccessGrant.objects.create(
            access_request=access_request,
            starts_at=now,
            expires_at=access_request.expires_at,
            is_active=True,
        )

    def preview_url(self, grant, document):
        return reverse(
            "employer_portal:document_view",
            kwargs={
                "token": grant.token,
                "document_id": document.id,
            },
        )

    def stream_url(self, grant, document):
        return reverse(
            "employer_portal:document_stream",
            kwargs={
                "token": grant.token,
                "document_id": document.id,
            },
        )

    def test_document_view_renders_secure_preview_page(self):
        document = self.create_document()
        grant = self.create_grant(document)

        response = self.client.get(self.preview_url(grant, document))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response,
            "employer_portal/document_preview.html",
        )
        self.assertContains(response, document.title)
        self.assertContains(response, "Secure document preview")
        self.assertContains(response, "Download copy")
        self.assertContains(response, "Back to portal")

        expected_stream_url = self.stream_url(grant, document)
        self.assertContains(response, expected_stream_url)

        # The private storage path must never be exposed to the employer.
        self.assertNotContains(response, document.file.name)

        self.assertTrue(
            AccessLog.objects.filter(
                access_request=grant.access_request,
                event_type=AccessLog.EventType.DOCUMENT_VIEWED,
                resource_identifier=str(document.id),
            ).exists()
        )

    def test_document_stream_returns_approved_file_inline(self):
        content = b"Private CV content"

        document = self.create_document(
            filename="current-cv.pdf",
            content=content,
        )
        grant = self.create_grant(document)

        response = self.client.get(self.stream_url(grant, document))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")
        self.assertTrue(
            response["Content-Disposition"].startswith(
                'inline; filename="'
            )
        )
        self.assertEqual(
            response["X-Content-Type-Options"],
            "nosniff",
        )
        self.assertEqual(
            response["Cache-Control"],
            "private, no-store, no-cache, must-revalidate",
        )
        self.assertEqual(
            response["Referrer-Policy"],
            "no-referrer",
        )

        streamed_content = b"".join(response.streaming_content)
        self.assertEqual(streamed_content, content)

    def test_unapproved_document_cannot_be_previewed_or_streamed(self):
        document = self.create_document()
        grant = self.create_grant(document)

        DocumentAccessRequest.objects.filter(
            access_request=grant.access_request,
            document=document,
        ).update(approved=False)

        preview_response = self.client.get(
            self.preview_url(grant, document)
        )
        stream_response = self.client.get(
            self.stream_url(grant, document)
        )

        self.assertEqual(preview_response.status_code, 404)
        self.assertEqual(stream_response.status_code, 404)

    def test_expired_grant_cannot_preview_or_stream_document(self):
        document = self.create_document()
        grant = self.create_grant(document)

        now = timezone.now()
        grant.starts_at = now - timedelta(days=2)
        grant.expires_at = now - timedelta(minutes=1)
        grant.save(update_fields=["starts_at", "expires_at"])

        preview_response = self.client.get(
            self.preview_url(grant, document)
        )
        stream_response = self.client.get(
            self.stream_url(grant, document)
        )

        self.assertEqual(preview_response.status_code, 404)
        self.assertEqual(stream_response.status_code, 404)

    def test_revoked_grant_cannot_preview_or_stream_document(self):
        document = self.create_document()
        grant = self.create_grant(document)

        grant.is_active = False
        grant.revoked_at = timezone.now()
        grant.save(update_fields=["is_active", "revoked_at"])

        preview_response = self.client.get(
            self.preview_url(grant, document)
        )
        stream_response = self.client.get(
            self.stream_url(grant, document)
        )

        self.assertEqual(preview_response.status_code, 404)
        self.assertEqual(stream_response.status_code, 404)
