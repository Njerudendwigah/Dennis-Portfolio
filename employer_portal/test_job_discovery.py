from datetime import datetime, timezone
from django.test import SimpleTestCase
from .job_discovery import normalize_external_job


class JobDiscoveryNormalizationTests(SimpleTestCase):
    def setUp(self):
        self.now = datetime(2026, 10, 10, 9, 0, tzinfo=timezone.utc)

    def make_job(self, **extra):
        item = {
            "title": "Warehouse & Distribution Supervisor",
            "companyName": "Example Logistics Ltd",
            "location": "Nairobi, Kenya",
            "country": "Kenya",
            "datePosted": "2026-10-09T08:30:00Z",
            "url": "https://devglobaljobs.com/jobs/warehouse-distribution-supervisor",
            "description": "Lead warehouse inventory accuracy, dispatch, stock control and distribution teams.",
        }
        item.update(extra)
        return normalize_external_job(item, now=self.now)

    def test_normalizes_fresh_nairobi_warehouse_role(self):
        record = self.make_job(currency="KES", salaryMin=65000, salaryMax=95000, salaryPeriod="monthly")
        self.assertIsNotNone(record)
        self.assertEqual(record["status"], "Discovered")
        self.assertEqual(record["source"], "Dev Global Jobs")
        self.assertEqual((record["salaryMin"], record["salaryMax"]), (65000, 95000))
        self.assertIn("warehouse", record["matchTerms"])

    def test_rejects_role_outside_target_counties(self):
        self.assertIsNone(self.make_job(location="Mombasa, Kenya"))

    def test_rejects_unrelated_job(self):
        self.assertIsNone(self.make_job(title="Social Media Designer", description="Create graphics and campaigns."))

    def test_rejects_old_job(self):
        self.assertIsNone(self.make_job(title="Procurement Officer", description="Procurement and supplier management.", datePosted="2026-08-01T08:30:00Z"))

    def test_does_not_show_foreign_salary_as_kes(self):
        record = self.make_job(currency="USD", salaryMin=3000, salaryMax=5000, salaryPeriod="monthly")
        self.assertIsNotNone(record)
        self.assertEqual((record["salaryMin"], record["salaryMax"]), ("", ""))

    def test_rejects_job_without_known_posting_date(self):
        self.assertIsNone(self.make_job(datePosted=""))
