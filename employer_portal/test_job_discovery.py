from datetime import datetime, timezone
from django.test import SimpleTestCase
from urllib.parse import parse_qs, urlparse
from .job_discovery import build_search_urls, normalize_external_job


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

    def test_normalizes_recent_nairobi_role_with_monthly_kes(self):
        record = self.make_job(currency="KES", salaryMin=65000, salaryMax=95000, salaryPeriod="monthly")
        self.assertIsNotNone(record)
        self.assertEqual(record["status"], "Discovered")
        self.assertEqual(record["source"], "Dev Global Jobs")
        self.assertEqual((record["salaryMin"], record["salaryMax"]), (65000, 95000))
        self.assertIn("warehouse", record["matchTerms"])
        self.assertEqual(record["matchLevel"], "Strong")

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

    def test_rejects_salary_without_explicit_monthly_or_annual_period(self):
        record = self.make_job(currency="KES", salaryMin=3000, salaryMax=5000)
        self.assertIsNotNone(record)
        self.assertEqual((record["salaryMin"], record["salaryMax"]), ("", ""))

    def test_rejects_job_without_known_posting_date(self):
        self.assertIsNone(self.make_job(datePosted=""))

    def test_does_not_assert_on_site_work_without_source_evidence(self):
        record = self.make_job()
        self.assertIsNotNone(record)
        self.assertEqual(record["workMode"], "Not specified")

    def test_accepts_remote_role_for_kenya(self):
        record = self.make_job(
            title="Inventory Systems Manager",
            location="",
            country="Kenya",
            workMode="Remote",
            description="Manage ERP, supply chain and inventory systems.",
        )
        self.assertIsNotNone(record)
        self.assertEqual(record["location"], "Remote, Kenya")
        self.assertEqual(record["workMode"], "Remote")

    def test_rejects_generic_country_only_location(self):
        self.assertIsNone(self.make_job(location="Kenya", title="Procurement Officer", description="Supplier management and stock control."))

    def test_search_urls_use_iso_country_and_unfiltered_fallback(self):
        urls = build_search_urls()
        self.assertEqual(len(urls), 20)
        queries = [parse_qs(urlparse(url).query) for url in urls]
        self.assertIn("ke", [query.get("country", [""])[0] for query in queries])
        self.assertTrue(any("country" not in query for query in queries))

    def test_infers_nairobi_from_an_explicit_location_label(self):
        record = self.make_job(
            location="Kenya",
            title="Procurement Officer",
            description="Job Location: Nairobi, Kenya. Manage stock control and supplier records.",
        )
        self.assertIsNotNone(record)
        self.assertEqual(record["location"], "Nairobi, Kenya")
