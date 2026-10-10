"""Private job discovery for the authenticated Job Hunt workspace.

Uses the public Dev Global Jobs API, keeps the provider's job-detail URL visible,
and does not submit applications or scrape sites that prohibit automated collection.
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta, timezone
from html import unescape
from urllib.parse import urlencode, urlparse
from urllib.request import Request, urlopen
import hashlib
import json
import re
from typing import Any

API_ROOT = "https://devglobaljobs.com/api/v1/jobs"
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


def normalize_external_job(item: dict[str, Any], source: str = "Dev Global Jobs",
                           now: datetime | None = None) -> dict[str, Any] | None:
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
        return None
    if not allowed_location(location, country, mode):
        inferred_location = infer_target_location(description)
        if inferred_location and (not location or location.strip().lower() in {"kenya", "ke", "ken"}):
            location = f"{inferred_location}, Kenya"
        else:
            return None

    terms = []
    score = 0
    for term in MATCH_TERMS:
        in_title = term in title.lower()
        in_description = term in description.lower()
        if in_title or in_description:
            terms.append(term)
            score += 3 if in_title else 1
    if not terms:
        return None

    posted = parse_date(first(item, "datePosted", "date_posted", "postedDate", "posted_date",
                              "pubDate", "pub_date", "datePublished", "date_published",
                              "publishedDate", "published_date", "postedAt", "posted_at",
                              "postingDate", "posting_date", "createdAt", "created_at",
                              "publishedAt", "published_at", "date_created"))
    if posted is None:
        return None
    current = now or datetime.now(timezone.utc)
    if current.tzinfo is None:
        current = current.replace(tzinfo=timezone.utc)
    age = current.astimezone(timezone.utc) - posted
    # Keep a modest ingestion window; the dashboard defaults to the requested last 48 hours.
    if age < timedelta(days=-1) or age > timedelta(days=30):
        return None

    closes = parse_date(first(item, "validThrough", "valid_through", "expiryDate", "expiry_date",
                              "closingDate", "closing_date", "deadline", "expiresAt", "expires_at"))
    url = clean(first(item, "url", "jobUrl", "job_url", "jobPageUrl", "job_page_url",
                      "permalink", "detailUrl", "detail_url", "link", "applicationLink", "application_link"))
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.hostname not in {"devglobaljobs.com", "www.devglobaljobs.com"}:
        return None

    salary_min, salary_max = monthly_kes(item)
    current_iso = current.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
    score_band = "Strong" if score >= 8 else "Good" if score >= 4 else "Potential"
    record_id = "discovered-" + hashlib.sha256(url.lower().rstrip("/").encode()).hexdigest()[:20]
    locationsource = location or "Location not specified"
    return {
        "id": record_id, "title": title[:180], "company": company[:180],
        "location": locationsource[:180],
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
        "notes": f"Automatically discovered via {source}. Profile keyword overlap: {', '.join(terms[:8])}. Confirm requirements and instructions on the source advert.",
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


def build_search_urls() -> list[str]:
    """Build ISO-country and unfiltered fallback queries for each search term."""
    urls = []
    for term in SEARCH_TERMS:
        urls.append(f"{API_ROOT}?{urlencode({'limit': 100, 'country': 'ke', 'search': term})}")
        urls.append(f"{API_ROOT}?{urlencode({'limit': 100, 'search': term})}")
    return urls


def collect_opportunities() -> dict[str, Any]:
    """Collect, normalize, location-filter and deduplicate recent vacancies."""
    # The provider's country page uses the ISO-style "ke" slug. The unfiltered
    # fallback ensures a country-parameter mismatch cannot silently return zero.
    queries = build_search_urls()
    jobs_by_url: dict[str, dict[str, Any]] = {}
    errors = []
    records_received = 0
    rejected_matches = 0

    def request_jobs(url: str) -> tuple[list[dict[str, Any]], str | None]:
        try:
            return _payload_items(_request_json(url)), None
        except Exception as exc:
            return [], str(exc)[:220]

    succeeded = 0
    with ThreadPoolExecutor(max_workers=min(6, len(queries))) as executor:
        futures = [executor.submit(request_jobs, url) for url in queries]
        for future in as_completed(futures):
            items, error = future.result()
            if error:
                errors.append(error)
                continue
            succeeded += 1
            records_received += len(items)
            for item in items:
                job = normalize_external_job(item)
                if job:
                    jobs_by_url.setdefault(job["jobUrl"].lower().rstrip("/"), job)
                else:
                    rejected_matches += 1

    jobs = sorted(
        jobs_by_url.values(),
        key=lambda row: parse_date(row["datePosted"]) or datetime.min.replace(tzinfo=timezone.utc),
        reverse=True,
    )[:120]
    return {
        "jobs": jobs,
        "sources": [{
            "name": "Dev Global Jobs",
            "ok": succeeded > 0,
            "count": len(jobs),
            "error": "" if succeeded else (errors[0] if errors else "No provider request succeeded."),
            "requestsSucceeded": succeeded,
            "requestsAttempted": len(queries),
        }],
        "diagnostics": {
            "queriesAttempted": len(queries),
            "queriesSucceeded": succeeded,
            "recordsReceived": records_received,
            "recordsMatched": len(jobs),
            "recordsRejectedByFilters": rejected_matches,
        },
        "scannedAt": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "recencyWindowDays": 30,
        "targetAreas": ["Nairobi County", "Kiambu County", "remote roles available in Kenya"],
        "disclaimer": "Confirm vacancy dates, salary, eligibility and instructions on the original advert. Salary appears only when the source identifies KES and a monthly or annual pay period. No application is submitted automatically.",
    }
