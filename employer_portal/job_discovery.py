"""Private job discovery for the authenticated Job Hunt workspace.

Uses the public Dev Global Jobs API, keeps the provider's job-detail URL visible,
and does not submit applications or scrape sites that prohibit automated collection.
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta, timezone
from html import unescape
from urllib.parse import parse_qs, urlencode, urljoin, urlparse
from urllib.request import Request, urlopen
import hashlib
import json
import re
import xml.etree.ElementTree as ET
from typing import Any

API_ROOT = "https://devglobaljobs.com/api/v1/jobs"
CAREER_POINT_FEEDS = (
    {
        "name": "Career Point Kenya · Nairobi jobs",
        "url": "https://www.careerpointkenya.co.ke/category/jobs-in-nairobi/feed/",
        "default_location": "Nairobi, Kenya",
        "allow_country_only": False,
    },
    {
        "name": "Career Point Kenya · Nairobi tag",
        "url": "https://www.careerpointkenya.co.ke/tag/jobs-in-nairobi/feed/",
        "default_location": "Nairobi, Kenya",
        "allow_country_only": False,
    },
    {
        "name": "Career Point Kenya · latest jobs",
        "url": "https://www.careerpointkenya.co.ke/feed/",
        "default_location": "",
        "allow_country_only": True,
    },
)
SEARCH_TERMS = ("warehouse", "storekeeper", "procurement", "supply chain", "inventory", "logistics", "distribution", "transport", "operations", "purchasing")
MATCH_TERMS = (
    "supply chain", "warehouse", "storekeeper", "stores", "inventory",
    "procurement", "purchasing", "distribution", "logistics", "transport",
    "fulfillment", "fulfilment", "stock control", "stock controller", "wms",
    "sap", "erp", "supplier", "vendor", "sourcing", "fleet", "dispatch",
    "materials", "operations", "supervisor", "manager", "grn", "lpo",
    "tender", "purchase order", "procurement compliance", "stock reconciliation",
    "warehouse management", "team leadership", "reporting",
)
OTHER_CITIES = (
    "mombasa", "nakuru", "kisumu", "eldoret", "nyeri", "meru", "garissa",
    "machakos", "kitui", "embu", "kakamega", "bungoma", "malindi", "voi",
)


def first(item: dict[str, Any], *keys: str) -> Any:
    return next((item.get(key) for key in keys if item.get(key) not in (None, "")), None)


def clean(value: Any) -> str:
    if isinstance(value, dict):
        value = first(value, "name", "value", "text", "city", "town", "locality",
                      "addressLocality", "region", "addressRegion", "country", "label")
    if isinstance(value, list):
        value = ", ".join(filter(None, (clean(part) for part in value)))
    value = unescape(str(value or ""))
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", value)).strip()


def parse_date(value: Any) -> datetime | None:
    if isinstance(value, dict):
        value = first(value, "datePosted", "value", "startDate")
    if value in (None, ""):
        return None
    if isinstance(value, str):
        relative = re.fullmatch(
            r"\s*(?:about\s+)?(just now|today|yesterday|\d+\s+(?:minutes?|hours?|days?|weeks?)\s+ago)\s*",
            value,
            re.IGNORECASE,
        )
        if relative:
            label = relative.group(1).lower()
            current = datetime.now(timezone.utc)
            if label == "just now" or label == "today":
                return current
            if label == "yesterday":
                return current - timedelta(days=1)
            amount, unit = re.match(r"(\d+)\s+(minutes?|hours?|days?|weeks?)\s+ago", label).groups()
            count = int(amount)
            delta = (
                timedelta(minutes=count) if unit.startswith("minute") else
                timedelta(hours=count) if unit.startswith("hour") else
                timedelta(days=count) if unit.startswith("day") else
                timedelta(weeks=count)
            )
            return current - delta
    if isinstance(value, (int, float)) or (isinstance(value, str) and value.strip().isdigit()):
        try:
            stamp = float(value)
            if stamp > 10_000_000_000:
                stamp /= 1000
            if stamp > 1_000_000_000:
                return datetime.fromtimestamp(stamp, timezone.utc)
        except (ValueError, OverflowError, OSError):
            return None
    raw = str(value).strip()
    try:
        date = datetime.fromisoformat(raw[:-1] + "+00:00" if raw.endswith("Z") else raw)
    except ValueError:
        date = None
        for pattern in ("%Y-%m-%d", "%d %b %Y", "%b %d, %Y", "%a, %d %b %Y %H:%M:%S %z"):
            try:
                date = datetime.strptime(raw, pattern)
                break
            except ValueError:
                pass
    if date is None:
        return None
    return (date.replace(tzinfo=timezone.utc) if date.tzinfo is None else date).astimezone(timezone.utc)


def location_text(item: dict[str, Any]) -> str:
    value = first(item, "location", "jobLocation", "job_location", "work_location",
                  "workLocation", "city", "city_name", "town", "town_name",
                  "workplace", "workPlace", "officeLocation", "locationName", "location_name")
    if isinstance(value, dict):
        address = value.get("address", value)
        if isinstance(address, dict):
            value = ", ".join(filter(None, (
                clean(first(address, "addressLocality", "city", "town", "locality")),
                clean(first(address, "addressRegion", "region", "state")),
                clean(first(address, "addressCountry", "country", "countryName")),
            )))
        else:
            value = address
    return clean(value)


def infer_target_location(description: str) -> str:
    """Read a city/county only when the job text explicitly labels it as a location."""
    places = r"Nairobi(?: County)?|Kiambu(?: County)?|Thika|Ruiru|Juja|Limuru|Kikuyu|Kahawa|Ruai"
    pattern = re.compile(
        rf"(?:job\s+location|work\s+location|location|based\s+in|located\s+in|"
        rf"position\s+based\s+in|office\s+in)\s*[:\-]?\s*({places})",
        re.IGNORECASE,
    )
    match = pattern.search(description or "")
    if not match:
        return ""
    return re.sub(r"\s+County$", "", match.group(1), flags=re.IGNORECASE)


def allowed_location(location: str, country: str, mode: str = "") -> bool:
    value = f"{location} {country} {mode}".lower()
    # Do not silently widen the user's county preference to any Kenyan county.
    if re.search(r"\b(?:" + "|".join(re.escape(city) for city in OTHER_CITIES) + r")\b", location, re.IGNORECASE):
        return False
    if any(place in value for place in (
        "nairobi", "kiambu", "thika", "ruiru", "juja", "limuru", "kikuyu", "kahawa", "ruai",
    )):
        return True
    return "remote" in value and ("kenya" in value or country.lower() in {"ke", "kenya", "ken"})


def monthly_kes(item: dict[str, Any]) -> tuple[int | None, int | None]:
    salary = item.get("baseSalary") or item.get("salary")
    if isinstance(salary, dict):
        value = salary.get("value", salary)
        value = value if isinstance(value, dict) else {}
        currency = clean(first(salary, "currency", "currencyCode") or first(item, "currency", "salaryCurrency"))
        low = first(value, "minValue", "minSalary", "minimum", "low") or first(item, "salaryMin", "salary_min", "minSalary")
        high = first(value, "maxValue", "maxSalary", "maximum", "high") or first(item, "salaryMax", "salary_max", "maxSalary")
        one = first(value, "value")
        if low is None and high is None and one is not None:
            low = high = one
        period = clean(first(value, "unitText", "unit", "salaryPeriod")
                       or first(item, "salaryPeriod", "salary_period", "payPeriod", "pay_period")).lower()
    else:
        currency = clean(first(item, "currency", "salaryCurrency", "salary_currency"))
        low = first(item, "salaryMin", "salary_min", "minSalary", "min_salary")
        high = first(item, "salaryMax", "salary_max", "maxSalary", "max_salary")
        period = clean(first(item, "salaryPeriod", "salary_period", "payPeriod", "pay_period")).lower()

    text = clean(first(item, "salaryText", "salary_text", "salaryRange", "salary_range"))
    if not currency and re.search(r"\bKES\b|\bKSH\b|KSh", text, re.I):
        currency = "KES"
    if low is None and high is None and text and currency.upper() in {"KES", "KSH", "KSHS"}:
        nums = [int(n.replace(",", "")) for n in re.findall(r"\d[\d,]*", text)]
        if nums and re.search(r"month|monthly|per month|/month", text, re.I):
            low, high = nums[0], (nums[1] if len(nums) > 1 else nums[0])
    # Never label foreign, unspecified-period, or unconfirmed salary values as KES/month.
    if currency.upper() not in {"KES", "KSH", "KSHS", "KSH."}:
        return None, None
    try:
        low_n = float(low) if low not in (None, "") else None
        high_n = float(high) if high not in (None, "") else None
    except (ValueError, TypeError):
        return None, None
    if "year" in period or "annual" in period:
        low_n = low_n / 12 if low_n is not None else None
        high_n = high_n / 12 if high_n is not None else None
    elif not any(word in period for word in ("month", "monthly", "mon")):
        return None, None
    return (
        int(round(low_n)) if low_n is not None and low_n >= 0 else None,
        int(round(high_n)) if high_n is not None and high_n >= 0 else None,
    )


def normalize_external_job(
    item: dict[str, Any],
    source: str = "Dev Global Jobs",
    now: datetime | None = None,
    allow_country_only_location: bool = False,
    diagnostics: dict[str, int] | None = None,
) -> dict[str, Any] | None:
    def reject(reason: str) -> None:
        if diagnostics is not None:
            diagnostics[reason] = diagnostics.get(reason, 0) + 1
        return None

    title = clean(first(item, "title", "jobTitle", "job_title", "position", "name"))
    company = clean(first(item, "company", "companyName", "company_name", "organisation",
                          "organization", "employer", "hiringOrganization")) or "Employer not specified"
    location = location_text(item)
    country = clean(first(item, "country", "countryName", "country_name", "countryCode", "country_code"))
    mode = clean(first(item, "workMode", "work_mode", "workplaceType", "workplace_type", "remote"))
    if "remote" in mode.lower() and not location:
        location = "Remote, Kenya"
    description = clean(first(item, "description", "jobDescription", "job_description",
                              "excerpt", "summary", "snippet"))
    if not title:
        return reject("missing_title")

    location_confidence = "City or remote location matched target"
    location_lower = location.strip().lower()
    if not allowed_location(location, country, mode):
        inferred_location = infer_target_location(description)
        if inferred_location and (not location or location_lower in {"kenya", "ke", "ken"}):
            location = f"{inferred_location}, Kenya"
            location_confidence = "Inferred from labelled advert text"
        elif allow_country_only_location and (
            country.lower() in {"ke", "kenya", "ken"}
            or location_lower in {"kenya", "ke", "ken"}
        ):
            # Keep country-level leads without pretending their city is Nairobi/Kiambu.
            location = "Kenya (city not specified)"
            location_confidence = "City unconfirmed — verify location before applying"
            if diagnostics is not None:
                diagnostics["accepted_country_only_location"] = diagnostics.get("accepted_country_only_location", 0) + 1
        else:
            return reject("location_not_target")

    terms = []
    score = 0
    for term in MATCH_TERMS:
        in_title = term in title.lower()
        in_description = term in description.lower()
        if in_title or in_description:
            terms.append(term)
            score += 3 if in_title else 1
    if not terms:
        return reject("no_profile_keyword_match")

    posted = parse_date(first(item, "datePosted", "date_posted", "postedDate", "posted_date",
                              "pubDate", "pub_date", "datePublished", "date_published",
                              "publishedDate", "published_date", "postedAt", "posted_at",
                              "postingDate", "posting_date", "createdAt", "created_at",
                              "publishedAt", "published_at", "date_created"))
    if posted is None:
        return reject("missing_or_unparseable_posting_date")
    current = now or datetime.now(timezone.utc)
    if current.tzinfo is None:
        current = current.replace(tzinfo=timezone.utc)
    age = current.astimezone(timezone.utc) - posted
    # Only return vacancies posted in the rolling 48 hours before this scan.
    # Existing older records remain in the private tracker, but are not refreshed as "new".
    if age < timedelta(0) or age > timedelta(hours=48):
        return reject("posting_date_outside_48_hour_window")

    closes = parse_date(first(item, "validThrough", "valid_through", "expiryDate", "expiry_date",
                              "closingDate", "closing_date", "deadline", "expiresAt", "expires_at"))
    url = clean(first(item, "url", "jobUrl", "job_url", "jobPageUrl", "job_page_url",
                      "permalink", "detailUrl", "detail_url", "link", "applicationLink", "application_link"))
    allowed_hosts = {
        "Dev Global Jobs": {"devglobaljobs.com", "www.devglobaljobs.com"},
        "Career Point Kenya": {"careerpointkenya.co.ke", "www.careerpointkenya.co.ke"},
    }.get(source, set())
    if url.startswith("/") and not url.startswith("//"):
        base = "https://www.careerpointkenya.co.ke" if source == "Career Point Kenya" else "https://devglobaljobs.com"
        url = urljoin(base, url)
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.hostname not in allowed_hosts:
        return reject("missing_or_unapproved_detail_url")

    salary_min, salary_max = monthly_kes(item)
    current_iso = current.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
    score_band = "Strong" if score >= 8 else "Good" if score >= 4 else "Potential"
    record_id = "discovered-" + hashlib.sha256(url.lower().rstrip("/").encode()).hexdigest()[:20]
    locationsource = location or "Location not specified"
    return {
        "id": record_id, "title": title[:180], "company": company[:180],
        "location": locationsource[:180],
        "locationConfidence": location_confidence,
        "workMode": "Remote" if "remote" in (location + " " + mode).lower()
                    else "Hybrid" if "hybrid" in mode.lower()
                    else "On-site" if "on-site" in mode.lower() or "onsite" in mode.lower()
                    else "Not specified",
        "datePosted": posted.isoformat().replace("+00:00", "Z"),
        "closingDate": closes.date().isoformat() if closes else "",
        "status": "Discovered", "source": source,
        "salaryMin": salary_min if salary_min is not None else "",
        "salaryMax": salary_max if salary_max is not None else "",
        "dateApplied": "", "followUpDate": "", "interviewDate": "", "contactName": "",
        "jobUrl": url, "sourceUrl": url, "jobDescription": description[:15000],
        "notes": (
            f"Automatically discovered via {source}. Profile keyword overlap: {', '.join(terms[:8])}. "
            + ("The source specifies Kenya but not a city; verify that this role is based in Nairobi/Kiambu or is remote before applying. "
               if location_confidence == "City unconfirmed — verify location before applying" else "")
            + "Confirm requirements and instructions on the source advert."
        ),
        "matchScore": score, "matchLevel": score_band, "matchTerms": terms,
        "createdAt": current_iso, "updatedAt": current_iso,
    }


def _request_json(url: str, timeout: int = 10) -> Any:
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.hostname not in {"devglobaljobs.com", "www.devglobaljobs.com"}:
        raise ValueError("Blocked non-approved job source URL.")
    request = Request(url, headers={
        "User-Agent": "DennisPortfolioJobSearch/1.0 (personal vacancy discovery)",
        "Accept": "application/json",
    })
    with urlopen(request, timeout=timeout) as response:
        raw = response.read(1_500_000)
    return json.loads(raw.decode("utf-8", errors="replace"))


def _payload_items(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if isinstance(payload, dict):
        for key in ("jobs", "results", "items", "opportunities", "data"):
            child = payload.get(key)
            if isinstance(child, list):
                return [item for item in child if isinstance(item, dict)]
            if isinstance(child, dict):
                found = _payload_items(child)
                if found:
                    return found
        if first(payload, "title", "jobTitle", "job_title", "position"):
            return [payload]
    return []


def _xml_child_text(node: ET.Element, *names: str) -> str:
    desired = {name.lower() for name in names}
    for child in node.iter():
        tag = child.tag.rsplit("}", 1)[-1].lower()
        if tag in desired:
            value = " ".join(part.strip() for part in child.itertext() if part.strip())
            if value:
                return value
    return ""


def parse_rss_jobs(
    raw_xml: bytes,
    feed_url: str,
    default_location: str = "",
) -> list[dict[str, Any]]:
    """Parse standard RSS 2.0 or Atom feed entries into the common job schema."""
    root = ET.fromstring(raw_xml)
    entries = [
        node for node in root.iter()
        if node.tag.rsplit("}", 1)[-1].lower() in {"item", "entry"}
    ]
    records: list[dict[str, Any]] = []
    for entry in entries:
        title = clean(_xml_child_text(entry, "title"))
        link = ""
        for child in entry.iter():
            if child.tag.rsplit("}", 1)[-1].lower() != "link":
                continue
            link = (child.attrib.get("href") or (child.text or "")).strip()
            if link:
                break
        link = urljoin(feed_url, link) if link else ""
        description = _xml_child_text(entry, "description", "summary", "encoded", "content")
        posted = _xml_child_text(entry, "pubdate", "published", "updated", "date")
        if not title or not link or not posted:
            continue

        company = ""
        # Career Point commonly appends "Job <employer>" to job titles.
        split_title = re.match(r"^(?P<title>.+?)\s+Job\s+(?P<company>.+)$", title, re.IGNORECASE)
        if split_title:
            title = split_title.group("title").strip()
            company = re.sub(r"^\s*(?:at\s+)", "", split_title.group("company")).strip()

        location = default_location
        if not location:
            location_match = re.search(
                r"(?:job\s+location|work\s+location|location)\s*[:\-]\s*"
                r"(Nairobi(?: County)?|Kiambu(?: County)?|Thika|Ruiru|Juja|Limuru|Kikuyu|Kahawa|Ruai)",
                description,
                re.IGNORECASE,
            )
            if location_match:
                location = location_match.group(1) + ", Kenya"
        records.append({
            "title": title,
            "companyName": company or "Employer not specified",
            "location": location,
            "country": "Kenya",
            "datePosted": posted,
            "url": link,
            "description": description,
        })
    return records


def _request_rss(url: str, default_location: str = "", timeout: int = 8) -> list[dict[str, Any]]:
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.hostname not in {
        "careerpointkenya.co.ke", "www.careerpointkenya.co.ke"
    }:
        raise ValueError("Blocked non-approved RSS source URL.")
    request = Request(url, headers={
        "User-Agent": "DennisPortfolioJobSearch/1.0 (personal job alerts; RSS reader)",
        "Accept": "application/rss+xml,application/atom+xml,application/xml,text/xml;q=0.9,*/*;q=0.8",
    })
    with urlopen(request, timeout=timeout) as response:
        raw = response.read(1_500_000)
    return parse_rss_jobs(raw, url, default_location)


def build_search_urls() -> list[str]:
    """Build ISO-country and unfiltered fallback queries for each search term."""
    urls = []
    for term in SEARCH_TERMS:
        urls.append(f"{API_ROOT}?{urlencode({'limit': 100, 'country': 'ke', 'search': term})}")
        urls.append(f"{API_ROOT}?{urlencode({'limit': 100, 'search': term})}")
    return urls


def collect_opportunities() -> dict[str, Any]:
    """Collect vacancies posted in the last 48 hours from the API and public RSS feeds."""
    queries = build_search_urls()
    jobs_by_url: dict[str, dict[str, Any]] = {}
    errors: list[str] = []
    reject_reasons: dict[str, int] = {}
    records_received = 0
    query_diagnostics: list[dict[str, Any]] = []

    def request_jobs(url: str) -> tuple[list[dict[str, Any]], str | None]:
        try:
            return _payload_items(_request_json(url)), None
        except Exception as exc:
            return [], str(exc)[:220]

    api_succeeded = 0
    futures_by_url = {}
    with ThreadPoolExecutor(max_workers=min(6, len(queries))) as executor:
        futures_by_url = {executor.submit(request_jobs, url): url for url in queries}
        for future in as_completed(futures_by_url):
            url = futures_by_url[future]
            items, error = future.result()
            params = parse_qs(urlparse(url).query)
            term = params.get("search", [""])[0]
            country_scope = params.get("country", [""])[0].lower() == "ke"
            query_row: dict[str, Any] = {
                "source": "Dev Global Jobs",
                "term": term,
                "countryScoped": country_scope,
                "received": len(items),
                "accepted": 0,
                "error": error or "",
            }
            if error:
                errors.append(error)
                query_diagnostics.append(query_row)
                continue

            api_succeeded += 1
            records_received += len(items)
            for item in items:
                job = normalize_external_job(
                    item,
                    source="Dev Global Jobs",
                    allow_country_only_location=country_scope,
                    diagnostics=reject_reasons,
                )
                if job:
                    query_row["accepted"] += 1
                    jobs_by_url.setdefault(job["jobUrl"].lower().rstrip("/"), job)
            query_diagnostics.append(query_row)

    rss_succeeded = 0
    rss_errors: list[str] = []

    def fetch_feed(feed: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]], str | None]:
        try:
            rows = _request_rss(feed["url"], feed.get("default_location", ""))
            return feed, rows, None
        except Exception as exc:
            return feed, [], str(exc)[:220]

    with ThreadPoolExecutor(max_workers=len(CAREER_POINT_FEEDS)) as executor:
        futures = [executor.submit(fetch_feed, feed) for feed in CAREER_POINT_FEEDS]
        for future in as_completed(futures):
            feed, items, error = future.result()
            query_row = {
                "source": "Career Point Kenya",
                "feed": feed["name"],
                "received": len(items),
                "accepted": 0,
                "error": error or "",
            }
            if error:
                rss_errors.append(error)
                errors.append(error)
                query_diagnostics.append(query_row)
                continue

            rss_succeeded += 1
            records_received += len(items)
            for item in items:
                job = normalize_external_job(
                    item,
                    source="Career Point Kenya",
                    allow_country_only_location=bool(feed.get("allow_country_only")),
                    diagnostics=reject_reasons,
                )
                if job:
                    query_row["accepted"] += 1
                    jobs_by_url.setdefault(job["jobUrl"].lower().rstrip("/"), job)
            query_diagnostics.append(query_row)

    jobs = sorted(
        jobs_by_url.values(),
        key=lambda row: parse_date(row["datePosted"]) or datetime.min.replace(tzinfo=timezone.utc),
        reverse=True,
    )[:250]

    counts = {"Dev Global Jobs": 0, "Career Point Kenya": 0}
    for job in jobs:
        counts[job["source"]] = counts.get(job["source"], 0) + 1

    source_status = [
        {
            "name": "Dev Global Jobs",
            "ok": api_succeeded > 0,
            "count": counts["Dev Global Jobs"],
            "error": "" if api_succeeded else (errors[0] if errors else "No API request succeeded."),
            "requestsSucceeded": api_succeeded,
            "requestsAttempted": len(queries),
        },
        {
            "name": "Career Point Kenya",
            "ok": rss_succeeded > 0,
            "count": counts["Career Point Kenya"],
            "error": "" if rss_succeeded else (rss_errors[0] if rss_errors else "No RSS feed returned data."),
            "feedsSucceeded": rss_succeeded,
            "feedsAttempted": len(CAREER_POINT_FEEDS),
        },
    ]

    return {
        "jobs": jobs,
        "sources": source_status,
        "diagnostics": {
            "queriesAttempted": len(queries) + len(CAREER_POINT_FEEDS),
            "queriesSucceeded": api_succeeded + rss_succeeded,
            "apiQueriesAttempted": len(queries),
            "apiQueriesSucceeded": api_succeeded,
            "feedsAttempted": len(CAREER_POINT_FEEDS),
            "feedsSucceeded": rss_succeeded,
            "recordsReceived": records_received,
            "recordsMatched": len(jobs),
            "recordsRejectedByFilters": sum(
                count for key, count in reject_reasons.items()
                if key != "accepted_country_only_location"
            ),
            "rejectReasons": reject_reasons,
            "queries": query_diagnostics,
        },
        "scannedAt": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "recencyWindowHours": 48,
        "targetAreas": ["Nairobi County", "Kiambu County", "remote roles available in Kenya"],
        "disclaimer": (
            "Only vacancies with a source posting time within the last 48 hours are returned. "
            "Country-only vacancies are marked for location verification. Confirm exact dates, salary, "
            "eligibility and instructions on the original advert. No application is submitted automatically."
        ),
    }
