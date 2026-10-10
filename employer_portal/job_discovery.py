"""Private vacancy discovery for the authenticated Job Hunt workspace."""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta, timezone
from html import unescape
from html.parser import HTMLParser
from urllib.parse import urlencode, urljoin, urlparse
from urllib.request import Request, urlopen
import hashlib
import json
import re
from typing import Any

DEV_GLOBAL_JOBS_API = "https://devglobaljobs.com/api/v1/jobs"
BRIGHTER_MONDAY_PAGES = (
    "https://www.brightermonday.co.ke/jobs/supply-chain-procurement/nairobi",
    "https://www.brightermonday.co.ke/jobs/manufacturing-warehousing/nairobi",
    "https://www.brightermonday.co.ke/jobs/shipping-logistics/nairobi",
)
SEARCH_TERMS = ("warehouse", "storekeeper", "procurement", "supply chain", "inventory", "logistics")
MATCH_TERMS = (
    "supply chain", "warehouse", "storekeeper", "stores", "inventory",
    "procurement", "purchasing", "distribution", "logistics", "transport",
    "fulfillment", "fulfilment", "stock control", "stock controller", "wms",
    "sap", "erp", "supplier", "vendor", "sourcing", "fleet", "dispatch",
    "materials", "operations", "supervisor", "manager", "grn", "lpo",
    "tender", "purchase order", "procurement compliance",
)
OTHER_CITIES = (
    "mombasa", "nakuru", "kisumu", "eldoret", "nyeri", "meru", "garissa",
    "machakos", "kitui", "embu", "kakamega", "bungoma", "malindi", "voi",
)


def first(item: dict[str, Any], *keys: str) -> Any:
    return next((item.get(key) for key in keys if item.get(key) not in (None, "")), None)


def clean(value: Any) -> str:
    if isinstance(value, dict):
        value = first(value, "name", "value", "text", "addressLocality", "addressRegion")
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
    value = first(item, "location", "jobLocation", "city", "workplace", "workPlace", "officeLocation")
    if isinstance(value, dict):
        value = value.get("address", value)
    if isinstance(value, dict):
        value = ", ".join(filter(None, (
            clean(first(value, "addressLocality", "city")),
            clean(first(value, "addressRegion", "region")),
            clean(first(value, "addressCountry", "country")),
        )))
    return clean(value)


def allowed_location(location: str, country: str) -> bool:
    lower = location.lower()
    if any(city in lower for city in OTHER_CITIES):
        return False
    all_text = (location + " " + country).lower()
    if any(term in all_text for term in (
        "nairobi", "kiambu", "thika", "ruiru", "juja", "limuru", "kikuyu",
        "kahawa", "ruai", "remote", "hybrid", "kenya",
    )):
        return True
    return country.lower() in {"ke", "kenya", "ken"} and not location


def monthly_kes(item: dict[str, Any]) -> tuple[int | None, int | None]:
    salary = item.get("baseSalary") or item.get("salary")
    if isinstance(salary, dict):
        value = salary.get("value", salary)
        value = value if isinstance(value, dict) else {}
        currency = clean(first(salary, "currency", "currencyCode") or first(item, "currency", "salaryCurrency"))
        low = first(value, "minValue", "minSalary", "minimum", "low")
        high = first(value, "maxValue", "maxSalary", "maximum", "high")
        one = first(value, "value")
        if low is None and high is None and one is not None:
            low = high = one
        period = clean(first(value, "unitText", "unit", "salaryPeriod") or first(item, "salaryPeriod", "payPeriod")).lower()
    else:
        currency = clean(first(item, "currency", "salaryCurrency"))
        low = first(item, "salaryMin", "minSalary")
        high = first(item, "salaryMax", "maxSalary")
        period = clean(first(item, "salaryPeriod", "payPeriod")).lower()
    text = clean(first(item, "salaryText", "salaryRange", "salary_text"))
    if not currency and re.search(r"\bKES\b|\bKSH\b|KSh", text, re.I):
        currency = "KES"
    if low is None and high is None and text and currency.upper() in {"KES", "KSH", "KSHS"}:
        nums = [int(n.replace(",", "")) for n in re.findall(r"\d[\d,]*", text)]
        if nums and re.search(r"month|monthly|per month|/month", text, re.I):
            low, high = nums[0], (nums[1] if len(nums) > 1 else nums[0])
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
    title = clean(first(item, "title", "jobTitle", "position", "name"))
    company = clean(first(item, "company", "companyName", "organisation", "organization", "employer", "hiringOrganization")) or "Employer not specified"
    location = location_text(item)
    country = clean(first(item, "country", "countryName", "countryCode"))
    if not location and country.lower() in {"ke", "kenya", "ken"}:
        location = "Kenya (city not specified)"
    desc = clean(first(item, "description", "jobDescription", "excerpt", "summary", "snippet"))
    if not title or not allowed_location(location, country):
        return None
    words = []
    score = 0
    for term in MATCH_TERMS:
        in_title, in_desc = term in title.lower(), term in desc.lower()
        if in_title or in_desc:
            words.append(term)
            score += 3 if in_title else 1
    if not words:
        return None
    posted = parse_date(first(item, "datePosted", "pubDate", "postedAt", "postingDate", "createdAt", "created_at", "publishedAt"))
    if posted is None:
        return None
    current = now or datetime.now(timezone.utc)
    if current.tzinfo is None:
        current = current.replace(tzinfo=timezone.utc)
    age = current.astimezone(timezone.utc) - posted
    if age < timedelta(days=-1) or age > timedelta(days=30):
        return None
    closes = parse_date(first(item, "validThrough", "expiryDate", "closingDate", "deadline", "expiresAt"))
    url = clean(first(item, "url", "jobUrl", "job_url", "jobPageUrl", "permalink", "detailUrl", "link", "applicationLink"))
    if url.startswith("/"):
        url = urljoin("https://www.brightermonday.co.ke" if source == "BrighterMonday" else "https://devglobaljobs.com", url)
    parsed = urlparse(url)
    if parsed.scheme != "https" or not parsed.netloc:
        return None
    low, high = monthly_kes(item)
    current_iso = current.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
    grade = "Strong" if score >= 8 else "Good" if score >= 4 else "Potential"
    record_id = "discovered-" + hashlib.sha256(f"{source}|{url.lower().rstrip('/')}".encode()).hexdigest()[:20]
    return {
        "id": record_id, "title": title[:180], "company": company[:180],
        "location": location[:180],
        "workMode": "Remote" if "remote" in location.lower() else "Hybrid" if "hybrid" in location.lower() else "On-site",
        "datePosted": posted.isoformat().replace("+00:00", "Z"),
        "closingDate": closes.date().isoformat() if closes else "",
        "status": "Discovered", "source": source,
        "salaryMin": low if low is not None else "", "salaryMax": high if high is not None else "",
        "dateApplied": "", "followUpDate": "", "interviewDate": "", "contactName": "",
        "jobUrl": url, "sourceUrl": url, "jobDescription": desc[:15000],
        "notes": f"Automatically discovered via {source}. CV keyword overlap: {', '.join(words[:8])}. Confirm requirements and application instructions on the source advert.",
        "matchScore": score, "matchLevel": grade, "matchTerms": words,
        "createdAt": current_iso, "updatedAt": current_iso,
    }


def _request_text(url: str, timeout: int = 8) -> str:
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.hostname not in {
        "devglobaljobs.com", "www.brightermonday.co.ke", "brightermonday.co.ke"
    }:
        raise ValueError("Blocked non-approved job source URL.")
    request = Request(url, headers={
        "User-Agent": "DennisPortfolioJobSearch/1.0 (personal vacancy discovery)",
        "Accept": "application/json,text/html,application/xhtml+xml;q=0.9,*/*;q=0.8",
    })
    with urlopen(request, timeout=timeout) as response:
        data = response.read(1_500_000)
        charset = response.headers.get_content_charset() or "utf-8"
    return data.decode(charset, errors="replace")


def _payload_items(value: Any) -> list[dict[str, Any]]:
    if isinstance(value, list):
        return [x for x in value if isinstance(x, dict)]
    if isinstance(value, dict):
        for key in ("jobs", "results", "items", "opportunities", "data"):
            child = value.get(key)
            if isinstance(child, list):
                return [x for x in child if isinstance(x, dict)]
            if isinstance(child, dict):
                found = _payload_items(child)
                if found:
                    return found
        if first(value, "title", "jobTitle", "position"):
            return [value]
    return []


class _JsonLdParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.capture = False
        self.buffer = []
        self.scripts = []

    def handle_starttag(self, tag, attrs):
        if tag.lower() == "script":
            attr = dict(attrs)
            self.capture = (attr.get("type") or "").lower() == "application/ld+json"
            self.buffer = []

    def handle_data(self, data):
        if self.capture:
            self.buffer.append(data)

    def handle_endtag(self, tag):
        if tag.lower() == "script" and self.capture:
            self.scripts.append("".join(self.buffer))
            self.buffer, self.capture = [], False


def _schema_jobs(value: Any) -> list[dict[str, Any]]:
    found = []
    if isinstance(value, dict):
        kinds = value.get("@type", [])
        kinds = kinds if isinstance(kinds, list) else [kinds]
        if any(str(kind).lower() == "jobposting" for kind in kinds):
            found.append(value)
        for child in value.values():
            if isinstance(child, (dict, list)):
                found.extend(_schema_jobs(child))
    elif isinstance(value, list):
        for child in value:
            found.extend(_schema_jobs(child))
    return found


def _get_brightermonday(url: str) -> list[dict[str, Any]]:
    parser = _JsonLdParser()
    parser.feed(_request_text(url))
    found = []
    for script in parser.scripts:
        try:
            found.extend(_schema_jobs(json.loads(script)))
        except (json.JSONDecodeError, TypeError):
            pass
    records = []
    for item in found:
        org = item.get("hiringOrganization") or {}
        loc = item.get("jobLocation") or {}
        if isinstance(loc, list):
            loc = loc[0] if loc else {}
        address = loc.get("address", loc) if isinstance(loc, dict) else loc
        salary = item.get("baseSalary") or {}
        salary_val = salary.get("value", {}) if isinstance(salary, dict) else {}
        records.append({
            "title": item.get("title"), "companyName": org.get("name") if isinstance(org, dict) else org,
            "location": location_text({"location": address}), "country": "Kenya",
            "datePosted": item.get("datePosted"), "validThrough": item.get("validThrough"),
            "description": item.get("description"), "url": item.get("url") or item.get("mainEntityOfPage") or url,
            "baseSalary": salary, "currency": salary.get("currency") if isinstance(salary, dict) else "",
            "salaryPeriod": salary_val.get("unitText") if isinstance(salary_val, dict) else "",
        })
    return records


def collect_opportunities() -> dict[str, Any]:
    tasks = []
    for term in SEARCH_TERMS:
        query = urlencode({"limit": 100, "country": "ke", "search": term})
        tasks.append(("Dev Global Jobs", "json", f"{DEV_GLOBAL_JOBS_API}?{query}"))
    tasks.extend(("BrighterMonday", "html", page) for page in BRIGHTER_MONDAY_PAGES)
    sources = {name: {"name": name, "ok": False, "count": 0, "error": ""}
               for name in ("Dev Global Jobs", "BrighterMonday")}
    records = {}

    def run(task):
        name, kind, url = task
        try:
            data = json.loads(_request_text(url)) if kind == "json" else None
            items = _payload_items(data) if kind == "json" else _get_brightermonday(url)
            return name, items, ""
        except Exception as exc:
            return name, [], str(exc)[:220]

    with ThreadPoolExecutor(max_workers=8) as pool:
        for future in as_completed([pool.submit(run, task) for task in tasks]):
            name, items, error = future.result()
            if error:
                if not sources[name]["error"]:
                    sources[name]["error"] = error
                continue
            sources[name]["ok"] = True
            for item in items:
                record = normalize_external_job(item, source=name)
                if record:
                    records.setdefault(record["jobUrl"].lower().rstrip("/"), record)
    jobs = sorted(records.values(), key=lambda row: parse_date(row["datePosted"]) or datetime.min.replace(tzinfo=timezone.utc), reverse=True)[:120]
    for job in jobs:
        sources[job["source"]]["count"] += 1
    for source in sources.values():
        if not source["ok"] and not source["error"]:
            source["error"] = "The source did not return usable data."
    return {
        "jobs": jobs, "sources": list(sources.values()),
        "scannedAt": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "recencyWindowDays": 30, "targetAreas": ["Nairobi County", "Kiambu County", "remote roles available in Kenya"],
        "disclaimer": "Confirm dates, salary, eligibility and instructions on the source listing. No application is submitted automatically.",
    }
