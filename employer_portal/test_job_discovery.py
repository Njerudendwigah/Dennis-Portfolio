from datetime import datetime, timezone
from django.test import SimpleTestCase
from urllib.parse import parse_qs, urlparse
from .job_discovery import build_search_urls, normalize_external_job, parse_rss_jobs


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

    def test_accepts_role_from_another_kenyan_county(self):
        record = self.make_job(location="Mombasa, Kenya")
        self.assertIsNotNone(record)
        self.assertEqual(record["location"], "Mombasa, Kenya")

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

    def test_accepts_country_only_role_with_location_warning(self):
        record = self.make_job(location="Kenya", title="Procurement Officer", description="Supplier management and stock control.")
        self.assertIsNotNone(record)
        self.assertEqual(record["location"], "Kenya (city not specified)")
        self.assertIn("verify location", record["locationConfidence"].lower())

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


    def test_includes_country_only_role_when_source_country_is_kenya(self):
        item = {
            "title": "Procurement Assistant",
            "companyName": "Example Organisation",
            "location": "Kenya",
            "country": "Kenya",
            "datePosted": "2026-10-09T08:30:00Z",
            "url": "https://devglobaljobs.com/jobs/detail/123456",
            "description": "Procurement, purchasing, stock records and supplier management.",
        }
        country_scoped = normalize_external_job(
            item, now=self.now, allow_country_only_location=True
        )
        general = normalize_external_job(item, now=self.now)
        self.assertIsNotNone(country_scoped)
        self.assertIsNotNone(general)
        self.assertEqual(general["location"], "Kenya (city not specified)")
        self.assertIn("verify location", general["locationConfidence"].lower())

    def test_converts_relative_posting_age(self):
        from .job_discovery import parse_date
        parsed = parse_date("2 days ago")
        self.assertIsNotNone(parsed)
        self.assertLess((datetime.now(timezone.utc) - parsed).total_seconds(), 3 * 86400)

    def test_accepts_relative_provider_detail_path(self):
        item = {
            "title": "Warehouse Supervisor",
            "companyName": "Example Organisation",
            "location": "Nairobi, Kenya",
            "country": "Kenya",
            "datePosted": "2026-10-09T08:30:00Z",
            "url": "/jobs/detail/123456",
            "description": "Warehouse, inventory, dispatch and stock control.",
        }
        record = normalize_external_job(item, now=self.now)
        self.assertIsNotNone(record)
        self.assertEqual(record["jobUrl"], "https://devglobaljobs.com/jobs/detail/123456")


    def test_rejects_job_older_than_48_hours(self):
        record = self.make_job(datePosted="2026-10-08T08:59:00Z")
        self.assertIsNone(record)

    def test_accepts_job_posted_within_48_hours(self):
        record = self.make_job(datePosted="2026-10-08T09:01:00Z")
        self.assertIsNotNone(record)

    def test_parses_career_point_rss_job_and_relative_link(self):
        feed = b"""<?xml version="1.0"?>
        <rss version="2.0"><channel><item>
          <title>Procurement Specialist - IT Job Techminds Technologies</title>
          <link>/2026/10/09/procurement-specialist/</link>
          <pubDate>Fri, 09 Oct 2026 11:00:00 +0300</pubDate>
          <description><![CDATA[Procurement and supplier management based in Nairobi.]]></description>
        </item></channel></rss>"""
        records = parse_rss_jobs(
            feed,
            "https://www.careerpointkenya.co.ke/category/jobs-in-nairobi/feed/",
            "Nairobi, Kenya",
        )
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["title"], "Procurement Specialist - IT")
        self.assertEqual(records[0]["companyName"], "Techminds Technologies")
        self.assertEqual(records[0]["url"], "https://www.careerpointkenya.co.ke/2026/10/09/procurement-specialist/")
        self.assertEqual(records[0]["datePosted"], "Fri, 09 Oct 2026 11:00:00 +0300")

    def test_rss_entries_without_post_dates_are_skipped(self):
        feed = b"""<rss version="2.0"><channel><item>
          <title>Warehouse Supervisor Job Example Ltd</title>
          <link>https://www.careerpointkenya.co.ke/jobs/example/</link>
          <description>Warehouse role in Nairobi.</description>
        </item></channel></rss>"""
        self.assertEqual(parse_rss_jobs(feed, "https://www.careerpointkenya.co.ke/feed/"), [])

    def test_accepts_city_only_location_from_country_scoped_feed(self):
        item = {
            "title": "Warehouse Supervisor",
            "companyName": "Example Logistics",
            "location": "Nakuru",
            "datePosted": "2026-10-10T08:00:00Z",
            "url": "https://devglobaljobs.com/jobs/nakuru-warehouse-supervisor",
            "description": "Manage warehouse stock control and dispatch teams.",
        }
        record = normalize_external_job(item, now=self.now, allow_country_only_location=True)
        self.assertIsNotNone(record)
        self.assertEqual(record["location"], "Nakuru, Kenya")
        self.assertIn("Kenya-wide feed", record["locationConfidence"])

    def test_rejects_explicit_foreign_country(self):
        record = self.make_job(
            title="Warehouse Supervisor",
            location="Kampala, Uganda",
            country="Uganda",
            description="Warehouse stock control and dispatch.",
        )
        self.assertIsNone(record)
