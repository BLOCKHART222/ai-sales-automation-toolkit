#!/usr/bin/env python3
"""
iConnect Sports — Automated Lead Generation Pipeline
=====================================================
End-to-end outbound lead generation: Apollo prospecting → email enrichment
→ Saleshandy sequence import → PhantomBuster LinkedIn auto-connect.

Built for iConnect Sports athlete partnership outreach.

Usage:
    python iconnect_pipeline.py run "FanDuel" "State Farm" "Novig"
    python iconnect_pipeline.py run --file companies.txt
    python iconnect_pipeline.py enrich --linkedin "https://linkedin.com/in/someone"
    python iconnect_pipeline.py enrich --file linkedin_urls.txt
    python iconnect_pipeline.py status
    python iconnect_pipeline.py daily

Author: Bryan Lockhart — iConnect Sports
"""

import argparse
import csv
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

# ─────────────────────────────────────────────────────────────────────────────
# .ENV LOADER — Reads key=value pairs from .env file (no dependencies needed)
# ─────────────────────────────────────────────────────────────────────────────

def load_dotenv(env_path=None):
    """Load environment variables from a .env file (stdlib only, no pip install)."""
    if env_path is None:
        env_path = Path(__file__).parent / ".env"
    if not Path(env_path).exists():
        return
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip("\"'")
            if key and key not in os.environ:  # Don't override existing env vars
                os.environ[key] = value

load_dotenv()

# ─────────────────────────────────────────────────────────────────────────────
# CONFIG — All secrets loaded from .env file (see .env.example for template)
# ─────────────────────────────────────────────────────────────────────────────

APOLLO_API_KEY = os.environ.get("APOLLO_API_KEY", "")
SALESHANDY_API_KEY = os.environ.get("SALESHANDY_API_KEY", "")
PB_API_KEY = os.environ.get("PB_API_KEY", "")
PB_AGENT_ID = os.environ.get("PB_AGENT_ID", "")
SH_SEQUENCE_ID = os.environ.get("SH_SEQUENCE_ID", "")
SH_STEP_ID = os.environ.get("SH_STEP_ID", "")

# File paths (relative to script directory)
SCRIPT_DIR = Path(__file__).parent
MASTER_CSV = SCRIPT_DIR / "iconnect_leads.csv"
PB_CSV = SCRIPT_DIR / "phantombuster_linkedin_upload.csv"
COMPANIES_FILE = SCRIPT_DIR / "target_companies.txt"
LOG_DIR = SCRIPT_DIR

# ─────────────────────────────────────────────────────────────────────────────
# TARGETING CONFIG
# ─────────────────────────────────────────────────────────────────────────────

# Companies to NEVER target
EXCLUSIONS = {
    "fanatics", "nike", "adidas", "puma", "bose", "beats by dre",
    "bleacher report", "espn", "wave sports", "overtime", "og esports",
}

# Title keywords to search for (in priority order)
TARGET_TITLES = [
    "marketing manager",
    "brand manager",
    "partnership manager",
    "sponsorship manager",
    "brand partnerships",
    "marketing director",
    "director of marketing",
    "director of partnerships",
    "director of sponsorships",
    "head of marketing",
    "head of partnerships",
]

# Seniority priority: 80% manager level, 20% director level
SENIORITY_TIERS = [
    {"seniorities": ["manager", "senior"], "ratio": 0.80, "label": "Manager"},
    {"seniorities": ["director"],          "ratio": 0.20, "label": "Director"},
]

MIN_LEADS_PER_COMPANY = 5

# ─────────────────────────────────────────────────────────────────────────────
# MARKET SEGMENTS — Each segment has its own targeting, titles, and company list
# ─────────────────────────────────────────────────────────────────────────────

SEGMENTS = {
    "big-corp": {
        "name": "Big Corporations",
        "description": "Athlete partnerships for major brand campaigns",
        "sales_cycle": "Long (3-6 months)",
        "titles": [
            "marketing manager", "brand manager", "partnership manager",
            "sponsorship manager", "brand partnerships", "marketing director",
            "director of marketing", "director of partnerships",
            "head of marketing", "head of partnerships",
        ],
        "seniority_split": [
            {"seniorities": ["manager", "senior"], "ratio": 0.80, "label": "Manager"},
            {"seniorities": ["director"],          "ratio": 0.20, "label": "Director"},
        ],
        "companies_file": "target_companies.txt",
    },
    "agencies": {
        "name": "Marketing Agencies",
        "description": "Strategic partners — offer iConnect as a white-label resource for their clients",
        "sales_cycle": "Medium (1-3 months)",
        "titles": [
            "account director", "client services director", "partnerships director",
            "vp client services", "managing director", "business development director",
            "account manager", "senior account manager", "partnership manager",
            "head of partnerships", "new business director",
        ],
        "seniority_split": [
            {"seniorities": ["manager", "senior"], "ratio": 0.80, "label": "Manager"},
            {"seniorities": ["director", "vp"],    "ratio": 0.20, "label": "Director/VP"},
        ],
        "companies_file": "target_agencies.txt",
    },
    "casinos": {
        "name": "Casinos",
        "description": "Sell athlete/player appearances, events, and promotions",
        "sales_cycle": "Medium (1-2 months)",
        "titles": [
            "entertainment director", "event manager", "marketing manager",
            "entertainment manager", "events director", "promotions manager",
            "vip marketing manager", "player development manager",
            "director of entertainment", "director of marketing",
        ],
        "seniority_split": [
            {"seniorities": ["manager", "senior"], "ratio": 0.80, "label": "Manager"},
            {"seniorities": ["director"],          "ratio": 0.20, "label": "Director"},
        ],
        "companies_file": "target_casinos.txt",
    },
    "smb": {
        "name": "Small-Mid Businesses",
        "description": "Local athlete partnerships — affordable packages",
        "sales_cycle": "Short (2-4 weeks)",
        "titles": [
            "owner", "founder", "ceo", "marketing manager",
            "marketing director", "head of marketing",
            "general manager", "brand manager",
        ],
        "seniority_split": [
            {"seniorities": ["owner", "founder"], "ratio": 0.50, "label": "Owner"},
            {"seniorities": ["manager", "senior"], "ratio": 0.30, "label": "Manager"},
            {"seniorities": ["director"],          "ratio": 0.20, "label": "Director"},
        ],
        "companies_file": "target_smb.txt",
    },
    "dealerships": {
        "name": "Car Dealerships",
        "description": "Athlete appearances for sales events and promotions",
        "sales_cycle": "Short (1-2 weeks)",
        "titles": [
            "general manager", "marketing manager", "marketing director",
            "events manager", "sales director", "owner",
            "managing partner", "dealer principal",
        ],
        "seniority_split": [
            {"seniorities": ["owner", "founder"], "ratio": 0.40, "label": "Owner/GM"},
            {"seniorities": ["manager", "senior"], "ratio": 0.40, "label": "Manager"},
            {"seniorities": ["director"],          "ratio": 0.20, "label": "Director"},
        ],
        "companies_file": "target_dealerships.txt",
    },
    "events": {
        "name": "Event Centers",
        "description": "Athlete appearances, meet & greets, hosted events",
        "sales_cycle": "Short-Medium",
        "titles": [
            "event director", "booking manager", "entertainment director",
            "events manager", "venue manager", "general manager",
            "programming director", "talent buyer",
        ],
        "seniority_split": [
            {"seniorities": ["manager", "senior"], "ratio": 0.80, "label": "Manager"},
            {"seniorities": ["director"],          "ratio": 0.20, "label": "Director"},
        ],
        "companies_file": "target_events.txt",
    },
    "high-adspend": {
        "name": "High Ad-Spend Companies",
        "description": "Companies with big marketing budgets — ROI on athlete content vs. traditional ads",
        "sales_cycle": "Medium",
        "titles": [
            "cmo", "vp marketing", "performance marketing director",
            "head of growth", "director of growth marketing",
            "marketing director", "head of brand marketing",
            "director of brand", "brand marketing manager",
        ],
        "seniority_split": [
            {"seniorities": ["manager", "senior"], "ratio": 0.60, "label": "Manager"},
            {"seniorities": ["director", "vp"],    "ratio": 0.40, "label": "Director/VP"},
        ],
        "companies_file": "target_high_adspend.txt",
    },
    "funded": {
        "name": "Recently Funded Startups",
        "description": "Fresh capital, brand building phase — catch them early",
        "sales_cycle": "Short-Medium",
        "titles": [
            "head of marketing", "marketing lead", "growth lead",
            "head of growth", "marketing manager", "brand manager",
            "cmo", "vp marketing", "founder", "ceo",
        ],
        "seniority_split": [
            {"seniorities": ["owner", "founder"], "ratio": 0.30, "label": "Founder"},
            {"seniorities": ["manager", "senior"], "ratio": 0.50, "label": "Manager"},
            {"seniorities": ["director", "vp"],    "ratio": 0.20, "label": "Director/VP"},
        ],
        "companies_file": "target_funded.txt",
    },
}

# ─────────────────────────────────────────────────────────────────────────────
# API HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def api_request(url, method="POST", data=None, headers=None):
    """Generic HTTP request helper using stdlib."""
    body = json.dumps(data).encode("utf-8") if data else None
    req = Request(url, data=body, headers=headers or {}, method=method)
    try:
        with urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except HTTPError as e:
        error_body = e.read().decode("utf-8", errors="replace")
        return {"error": True, "status": e.code, "message": error_body}
    except URLError as e:
        return {"error": True, "status": 0, "message": str(e.reason)}


def print_header(title):
    width = 60
    print(f"\n{'=' * width}")
    print(f"  iConnect Sports — {title}")
    print(f"{'=' * width}\n")


def print_lead_table(leads, start=1):
    """Print leads in the required numbered format."""
    if not leads:
        print("  No leads to display.\n")
        return
    for i, lead in enumerate(leads, start):
        name = f"{lead.get('first_name', '')} {lead.get('last_name', '')}".strip()
        title = lead.get("title", "—")
        company = lead.get("company", "—")
        email = lead.get("email", "—")
        linkedin = lead.get("linkedin_url", "—")
        print(f"  {i}. {name} | {title} | {company} | {email} | {linkedin}")
    print()


# ─────────────────────────────────────────────────────────────────────────────
# APOLLO API CLIENT
# ─────────────────────────────────────────────────────────────────────────────

class ApolloClient:
    """Wrapper for Apollo.io REST API — prospecting and enrichment."""

    BASE_URL = "https://api.apollo.io/v1"

    def __init__(self, api_key):
        self.api_key = api_key
        self.headers = {
            "Content-Type": "application/json",
            "Cache-Control": "no-cache",
        }

    def search_people(self, domain, titles=None, seniorities=None, limit=10):
        """
        Search for people at a company by domain.

        Args:
            domain: Company domain (e.g., 'fanduel.com')
            titles: List of title keywords to filter by
            seniorities: List of seniority levels ('manager', 'senior', 'director')
            limit: Max results to return

        Returns:
            List of people dicts with name, title, email, linkedin_url
        """
        url = f"{self.BASE_URL}/mixed_people/search"
        payload = {
            "api_key": self.api_key,
            "q_organization_domains_list": [domain],
            "page": 1,
            "per_page": limit,
        }

        if titles:
            payload["q_keywords"] = " OR ".join(titles)
        if seniorities:
            payload["person_seniorities"] = seniorities

        result = api_request(url, data=payload, headers=self.headers)

        if result.get("error"):
            print(f"    [Apollo Error] {result.get('message', 'Unknown error')}")
            return []

        people = result.get("people", [])
        leads = []
        for person in people:
            lead = {
                "first_name": person.get("first_name", ""),
                "last_name": person.get("last_name", ""),
                "title": person.get("title", ""),
                "company": person.get("organization", {}).get("name", ""),
                "email": person.get("email", ""),
                "email_status": person.get("email_status", ""),
                "linkedin_url": person.get("linkedin_url", ""),
                "apollo_id": person.get("id", ""),
            }
            leads.append(lead)

        return leads

    def enrich_by_linkedin(self, linkedin_url):
        """
        Enrich a person by their LinkedIn URL.

        Args:
            linkedin_url: Full LinkedIn profile URL

        Returns:
            Lead dict or None
        """
        url = f"{self.BASE_URL}/people/match"
        payload = {
            "api_key": self.api_key,
            "linkedin_url": linkedin_url,
            "reveal_personal_emails": False,
        }

        result = api_request(url, data=payload, headers=self.headers)

        if result.get("error"):
            print(f"    [Apollo Error] {result.get('message', 'Unknown error')}")
            return None

        person = result.get("person")
        if not person:
            print(f"    [Apollo] No match found for {linkedin_url}")
            return None

        return {
            "first_name": person.get("first_name", ""),
            "last_name": person.get("last_name", ""),
            "title": person.get("title", ""),
            "company": person.get("organization", {}).get("name", ""),
            "email": person.get("email", ""),
            "email_status": person.get("email_status", ""),
            "linkedin_url": person.get("linkedin_url", linkedin_url),
            "apollo_id": person.get("id", ""),
        }

    def enrich_batch(self, linkedin_urls):
        """Enrich multiple LinkedIn URLs."""
        results = []
        for url in linkedin_urls:
            print(f"    Enriching: {url}")
            lead = self.enrich_by_linkedin(url)
            if lead:
                results.append(lead)
            time.sleep(0.5)  # Rate limit buffer
        return results


# ─────────────────────────────────────────────────────────────────────────────
# SALESHANDY API CLIENT
# ─────────────────────────────────────────────────────────────────────────────

class SaleshandyClient:
    """Wrapper for Saleshandy REST API — sequence management and imports."""

    BASE_URL = "https://api.saleshandy.com/api/v1"

    def __init__(self, api_key):
        self.api_key = api_key
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

    def import_to_sequence(self, step_id, leads, verify=True):
        """
        Import leads into a Saleshandy sequence step.

        Args:
            step_id: The sequence step ID
            leads: List of lead dicts
            verify: Whether to verify email addresses

        Returns:
            Import response dict with requestId
        """
        url = f"{self.BASE_URL}/prospects/import"
        prospects = []
        for lead in leads:
            if not lead.get("email"):
                continue  # Skip leads without email
            prospects.append({
                "First Name": lead.get("first_name", ""),
                "Last Name": lead.get("last_name", ""),
                "Email": lead["email"],
                "Company": lead.get("company", ""),
                "Job Title": lead.get("title", ""),
            })

        if not prospects:
            print("    No leads with emails to import.")
            return None

        payload = {
            "stepId": step_id,
            "prospectList": prospects,
            "conflictAction": "noUpdate",
            "verifyProspects": verify,
        }

        result = api_request(url, data=payload, headers=self.headers)

        if result.get("error"):
            print(f"    [Saleshandy Error] {result.get('message', 'Unknown error')}")
            return None

        request_id = result.get("payload", {}).get("requestId", "")
        print(f"    Import started — requestId: {request_id}")
        return result

    def check_import_status(self, request_id):
        """Check the status of a prospect import."""
        url = f"{self.BASE_URL}/prospects/import-status/{request_id}"
        return api_request(url, method="GET", headers=self.headers)


# ─────────────────────────────────────────────────────────────────────────────
# PHANTOMBUSTER CLIENT
# ─────────────────────────────────────────────────────────────────────────────

class PhantomBusterClient:
    """Wrapper for PhantomBuster API — LinkedIn auto-connect agent."""

    BASE_URL = "https://api.phantombuster.com/api/v2"

    def __init__(self, api_key, agent_id):
        self.api_key = api_key
        self.agent_id = agent_id
        self.headers = {
            "X-Phantombuster-Key": api_key,
            "Content-Type": "application/json",
        }

    def get_status(self):
        """Check phantom agent status."""
        url = f"{self.BASE_URL}/agents/fetch?id={self.agent_id}"
        return api_request(url, method="GET", headers=self.headers)

    def launch(self):
        """Trigger an immediate phantom launch."""
        url = f"{self.BASE_URL}/agents/launch"
        return api_request(url, data={"id": self.agent_id}, headers=self.headers)


# ─────────────────────────────────────────────────────────────────────────────
# LEAD MANAGER — CSV tracking, dedup, exports
# ─────────────────────────────────────────────────────────────────────────────

class LeadManager:
    """Manages the master lead CSV, dedup, and export files."""

    MASTER_HEADERS = [
        "Date Added", "First Name", "Last Name", "Title", "Company",
        "Email", "LinkedIn URL", "Email Status", "LinkedIn Status", "Notes",
    ]

    PB_HEADERS = ["linkedInUrl", "firstName", "lastName", "company", "title"]

    def __init__(self, master_csv, pb_csv):
        self.master_csv = Path(master_csv)
        self.pb_csv = Path(pb_csv)
        self._existing_emails = set()
        self._existing_linkedin = set()
        self._load_existing()

    def _load_existing(self):
        """Load existing emails and LinkedIn URLs for dedup."""
        if self.master_csv.exists():
            with open(self.master_csv, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    email = (row.get("Email") or "").strip().lower()
                    linkedin = (row.get("LinkedIn URL") or "").strip().lower()
                    if email:
                        self._existing_emails.add(email)
                    if linkedin:
                        self._existing_linkedin.add(linkedin)
        print(f"  Loaded {len(self._existing_emails)} existing emails, "
              f"{len(self._existing_linkedin)} LinkedIn URLs for dedup.")

    def is_duplicate(self, lead):
        """Check if a lead already exists in the master CSV."""
        email = (lead.get("email") or "").strip().lower()
        linkedin = (lead.get("linkedin_url") or "").strip().lower()
        if email and email in self._existing_emails:
            return True
        if linkedin and linkedin in self._existing_linkedin:
            return True
        return False

    def deduplicate(self, leads):
        """Remove duplicates from a list of leads."""
        unique = []
        seen = set()
        for lead in leads:
            email = (lead.get("email") or "").strip().lower()
            linkedin = (lead.get("linkedin_url") or "").strip().lower()
            key = email or linkedin or f"{lead.get('first_name', '')}-{lead.get('last_name', '')}-{lead.get('company', '')}"

            if key in seen or self.is_duplicate(lead):
                continue
            seen.add(key)
            unique.append(lead)
        return unique

    def append_to_master(self, leads, notes=""):
        """Append leads to the master CSV."""
        today = datetime.now().strftime("%Y-%m-%d")
        file_exists = self.master_csv.exists() and self.master_csv.stat().st_size > 0

        with open(self.master_csv, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(self.MASTER_HEADERS)

            for lead in leads:
                email = lead.get("email", "")
                linkedin = lead.get("linkedin_url", "")
                email_status = "Queued" if email else "—"
                linkedin_status = "Pending"
                writer.writerow([
                    today,
                    lead.get("first_name", ""),
                    lead.get("last_name", ""),
                    lead.get("title", ""),
                    lead.get("company", ""),
                    email,
                    linkedin,
                    email_status,
                    linkedin_status,
                    notes,
                ])
                # Update dedup sets
                if email:
                    self._existing_emails.add(email.lower())
                if linkedin:
                    self._existing_linkedin.add(linkedin.lower())

        print(f"  Appended {len(leads)} leads to {self.master_csv.name}")

    def append_to_phantombuster(self, leads):
        """Append leads with LinkedIn URLs to the PhantomBuster CSV."""
        linkedin_leads = [l for l in leads if l.get("linkedin_url")]
        if not linkedin_leads:
            print("  No leads with LinkedIn URLs for PhantomBuster.")
            return 0

        file_exists = self.pb_csv.exists() and self.pb_csv.stat().st_size > 0

        with open(self.pb_csv, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(self.PB_HEADERS)

            for lead in linkedin_leads:
                writer.writerow([
                    lead.get("linkedin_url", ""),
                    lead.get("first_name", ""),
                    lead.get("last_name", ""),
                    lead.get("company", ""),
                    lead.get("title", ""),
                ])

        print(f"  Appended {len(linkedin_leads)} leads to {self.pb_csv.name}")
        return len(linkedin_leads)

    def get_lead_count(self):
        """Return total leads in master CSV."""
        if not self.master_csv.exists():
            return 0
        with open(self.master_csv, "r", encoding="utf-8") as f:
            return sum(1 for _ in f) - 1  # Subtract header


# ─────────────────────────────────────────────────────────────────────────────
# DAILY LOG
# ─────────────────────────────────────────────────────────────────────────────

def write_daily_log(log_dir, leads_added, companies_searched, shortfall_companies):
    """Write a daily pipeline log."""
    today = datetime.now().strftime("%Y-%m-%d")
    log_path = Path(log_dir) / f"iconnect_daily_log_{today}.txt"

    email_leads = [l for l in leads_added if l.get("email")]
    linkedin_only = [l for l in leads_added if l.get("linkedin_url") and not l.get("email")]

    lines = [
        "=" * 64,
        f"  iConnect Sports — Daily Pipeline Log — {today}",
        "=" * 64,
        "",
        "SUMMARY",
        "-------",
        f"Companies searched:  {len(companies_searched)}",
        f"Leads with email:    {len(email_leads)}",
        f"LinkedIn-only leads: {len(linkedin_only)}",
        f"Total new leads:     {len(leads_added)}",
        "",
        "LEADS ADDED (with email → Saleshandy)",
        "-" * 45,
    ]

    for i, lead in enumerate(email_leads, 1):
        name = f"{lead.get('first_name', '')} {lead.get('last_name', '')}".strip()
        lines.append(f"  {i}. {name} | {lead.get('title', '')} | "
                      f"{lead.get('company', '')} | {lead.get('email', '')}")

    if linkedin_only:
        lines.append("")
        lines.append("LINKEDIN-ONLY LEADS (PhantomBuster only)")
        lines.append("-" * 45)
        for i, lead in enumerate(linkedin_only, 1):
            name = f"{lead.get('first_name', '')} {lead.get('last_name', '')}".strip()
            lines.append(f"  {i}. {name} | {lead.get('title', '')} | "
                          f"{lead.get('company', '')}")

    if shortfall_companies:
        lines.append("")
        lines.append("COMPANIES UNDER MINIMUM (need manual LinkedIn search)")
        lines.append("-" * 52)
        for company, count in shortfall_companies.items():
            needed = MIN_LEADS_PER_COMPANY - count
            lines.append(f"  {company}: have {count}, need {needed} more")

    lines.append("")
    lines.append("=" * 64)

    with open(log_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    print(f"  Daily log written: {log_path.name}")
    return log_path


# ─────────────────────────────────────────────────────────────────────────────
# PIPELINE — Core orchestration
# ─────────────────────────────────────────────────────────────────────────────

class Pipeline:
    """Main pipeline orchestrator — ties Apollo, Saleshandy, and PB together."""

    def __init__(self):
        self.apollo = ApolloClient(APOLLO_API_KEY)
        self.saleshandy = SaleshandyClient(SALESHANDY_API_KEY)
        self.phantombuster = PhantomBusterClient(PB_API_KEY, PB_AGENT_ID)
        self.leads = LeadManager(MASTER_CSV, PB_CSV)
        self.all_new_leads = []
        self.shortfall_companies = {}

    def _is_excluded(self, company):
        """Check if a company is on the exclusion list."""
        return company.strip().lower() in EXCLUSIONS

    def set_segment(self, segment_key):
        """Load targeting config for a specific market segment."""
        if segment_key not in SEGMENTS:
            print(f"  [ERROR] Unknown segment: {segment_key}")
            print(f"  Available: {', '.join(SEGMENTS.keys())}")
            return False

        seg = SEGMENTS[segment_key]
        self.active_segment = segment_key
        self.segment_titles = seg["titles"]
        self.segment_seniority = seg["seniority_split"]
        print(f"  Segment: {seg['name']}")
        print(f"  Pitch:   {seg['description']}")
        print(f"  Cycle:   {seg['sales_cycle']}")
        print()
        return True

    def _search_company(self, company, domain=None):
        """
        Search Apollo for leads at a single company.
        Uses the active segment's seniority tiers and title filters.
        """
        if self._is_excluded(company):
            print(f"  ⚠  {company} is excluded — skipping.")
            return []

        if not domain:
            domain = company.lower().replace(" ", "") + ".com"

        print(f"\n  Searching: {company} ({domain})")
        print(f"  {'─' * 50}")

        # Use segment config or defaults
        seniority_tiers = getattr(self, "segment_seniority", SENIORITY_TIERS)
        titles = getattr(self, "segment_titles", TARGET_TITLES)

        all_leads = []
        target_total = MIN_LEADS_PER_COMPANY

        for tier in seniority_tiers:
            tier_target = max(1, round(target_total * tier["ratio"]))
            remaining = target_total - len(all_leads)
            fetch_count = min(tier_target, remaining) if remaining > 0 else 0

            if fetch_count <= 0:
                break

            # Split titles by tier — managers get first half, directors get second half
            mid = len(titles) // 2
            tier_titles = titles[:mid] if "manager" in tier["seniorities"] or "owner" in tier["seniorities"] else titles[mid:]

            print(f"    [{tier['label']} tier] Searching for {fetch_count} leads "
                  f"(seniority: {', '.join(tier['seniorities'])})")

            leads = self.apollo.search_people(
                domain=domain,
                titles=tier_titles,
                seniorities=tier["seniorities"],
                limit=fetch_count + 5,
            )

            new_leads = self.leads.deduplicate(leads)
            all_leads.extend(new_leads[:fetch_count])

            print(f"    Found {len(leads)} raw → {len(new_leads)} after dedup")
            time.sleep(0.3)

        if len(all_leads) < MIN_LEADS_PER_COMPANY:
            shortfall = MIN_LEADS_PER_COMPANY - len(all_leads)
            self.shortfall_companies[company] = len(all_leads)
            print(f"    ⚠  Only {len(all_leads)} leads found — need {shortfall} more.")
            print(f"    → Flagged for manual LinkedIn search.")

        return all_leads

    def run_search(self, companies):
        """
        Run the full search pipeline for a list of companies.

        Args:
            companies: List of (company_name, domain) tuples or just company names
        """
        print_header("Lead Search Pipeline")

        # Validate API key
        if not APOLLO_API_KEY:
            print("  [ERROR] Apollo API key not set!")
            print("  Set APOLLO_API_KEY environment variable or edit config in this file.")
            return

        total_leads = []

        for entry in companies:
            if isinstance(entry, tuple):
                company, domain = entry
            else:
                company = entry
                domain = None

            if self._is_excluded(company):
                print(f"\n  ⚠  Skipping excluded company: {company}")
                continue

            leads = self._search_company(company, domain)
            total_leads.extend(leads)

        if not total_leads:
            print("\n  No new leads found across all companies.")
            return

        # Deduplicate the full batch
        unique_leads = self.leads.deduplicate(total_leads)
        self.all_new_leads.extend(unique_leads)

        # Display results
        print_header("New Leads Found")
        print_lead_table(unique_leads)

        # Import to systems
        self._import_leads(unique_leads)

        # Write daily log
        searched = [c[0] if isinstance(c, tuple) else c for c in companies]
        write_daily_log(LOG_DIR, unique_leads, searched, self.shortfall_companies)

        # Final summary
        self._print_summary(unique_leads)

    def enrich_linkedin(self, linkedin_urls):
        """
        Enrich LinkedIn URLs via Apollo and import results.

        Args:
            linkedin_urls: List of LinkedIn profile URLs
        """
        print_header("LinkedIn Enrichment")

        if not APOLLO_API_KEY:
            print("  [ERROR] Apollo API key not set!")
            return

        leads = self.apollo.enrich_batch(linkedin_urls)
        unique_leads = self.leads.deduplicate(leads)

        if not unique_leads:
            print("  No new leads after enrichment + dedup.")
            return

        print_header("Enriched Leads")
        print_lead_table(unique_leads)

        self._import_leads(unique_leads)
        self._print_summary(unique_leads)

    def _import_leads(self, leads):
        """Import leads to Saleshandy and PhantomBuster."""
        email_leads = [l for l in leads if l.get("email")]

        # Saleshandy import (email leads only)
        if email_leads and SALESHANDY_API_KEY:
            print(f"\n  Importing {len(email_leads)} leads to Saleshandy...")
            self.saleshandy.import_to_sequence(SH_STEP_ID, email_leads)
        elif email_leads:
            print("\n  ⚠  Saleshandy API key not set — skipping email import.")
            print("  Set SALESHANDY_API_KEY environment variable or edit config.")

        # Append to master CSV
        self.leads.append_to_master(leads)

        # Append to PhantomBuster CSV
        self.leads.append_to_phantombuster(leads)

    def _print_summary(self, leads):
        """Print final pipeline summary."""
        email_count = len([l for l in leads if l.get("email")])
        linkedin_count = len([l for l in leads if l.get("linkedin_url")])

        print_header("Pipeline Summary")
        print(f"  New leads processed:     {len(leads)}")
        print(f"  With verified email:     {email_count} → Saleshandy")
        print(f"  With LinkedIn URL:       {linkedin_count} → PhantomBuster")
        print(f"  Total in master CSV:     {self.leads.get_lead_count()}")

        if self.shortfall_companies:
            print(f"\n  ⚠  Companies needing manual LinkedIn search:")
            for company, count in self.shortfall_companies.items():
                needed = MIN_LEADS_PER_COMPANY - count
                print(f"     → {company}: have {count}, need {needed} more")

        print()

    def show_status(self):
        """Show current pipeline status."""
        print_header("Pipeline Status")

        lead_count = self.leads.get_lead_count()
        print(f"  Master CSV leads:  {lead_count}")
        print(f"  Master CSV path:   {MASTER_CSV}")
        print(f"  PB CSV path:       {PB_CSV}")
        print()

        # Check API keys
        apollo_ok = bool(APOLLO_API_KEY)
        sh_ok = bool(SALESHANDY_API_KEY)
        pb_ok = bool(PB_API_KEY)

        print(f"  API Keys:")
        print(f"    Apollo:       {'✓ Set' if apollo_ok else '✗ Not set'}")
        print(f"    Saleshandy:   {'✓ Set' if sh_ok else '✗ Not set'}")
        print(f"    PhantomBuster: {'✓ Set' if pb_ok else '✗ Set'}")
        print()

        print(f"  Exclusions: {', '.join(sorted(EXCLUSIONS))}")
        print(f"  Min leads/company: {MIN_LEADS_PER_COMPANY}")
        print(f"  Seniority split: 80% manager / 20% director")
        print()

    def run_daily(self):
        """
        Run the full daily pipeline from the active segment's companies file.
        Reads companies from the segment's target file (one per line, format: Company Name, domain.com)
        """
        print_header("Daily Pipeline Run")

        # Use the segment-specific companies file if set
        seg_key = getattr(self, "active_segment", "big-corp")
        seg = SEGMENTS.get(seg_key, {})
        companies_file = SCRIPT_DIR / seg.get("companies_file", "target_companies.txt")

        if not companies_file.exists():
            print(f"  [ERROR] Companies file not found: {companies_file}")
            print(f"  Create '{companies_file.name}' with one company per line:")
            print(f"    FanDuel, fanduel.com")
            print(f"    State Farm, statefarm.com")
            print(f"    Novig, novig.co")
            return

        companies = []
        with open(companies_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "," in line:
                    parts = [p.strip() for p in line.split(",", 1)]
                    companies.append((parts[0], parts[1]))
                else:
                    companies.append(line)

        print(f"  Loaded {len(companies)} companies from {companies_file.name}")
        print(f"  Segment: {seg.get('name', 'Default')}")
        self.run_search(companies)


# ─────────────────────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="iConnect Sports — Automated Lead Generation Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python iconnect_pipeline.py run "FanDuel" "State Farm"
  python iconnect_pipeline.py run --file companies.txt
  python iconnect_pipeline.py enrich --linkedin "https://linkedin.com/in/someone"
  python iconnect_pipeline.py enrich --file linkedin_urls.txt
  python iconnect_pipeline.py daily
  python iconnect_pipeline.py status
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Pipeline command")

    # Segment names for help text
    seg_names = ", ".join(SEGMENTS.keys())

    # run — search companies for leads
    run_parser = subparsers.add_parser("run", help="Search companies for leads")
    run_parser.add_argument("companies", nargs="*", help="Company names to search")
    run_parser.add_argument("--file", "-f", help="File with company names (one per line)")
    run_parser.add_argument("--segment", "-s", default="big-corp",
                            help=f"Market segment ({seg_names}). Default: big-corp")

    # enrich — enrich LinkedIn URLs
    enrich_parser = subparsers.add_parser("enrich", help="Enrich LinkedIn URLs via Apollo")
    enrich_parser.add_argument("--linkedin", "-l", nargs="+", help="LinkedIn URLs to enrich")
    enrich_parser.add_argument("--file", "-f", help="File with LinkedIn URLs (one per line)")

    # daily — run full daily pipeline
    daily_parser = subparsers.add_parser("daily", help="Run full daily pipeline from target file")
    daily_parser.add_argument("--segment", "-s", default="big-corp",
                              help=f"Market segment ({seg_names}). Default: big-corp")

    # segments — list all available segments
    subparsers.add_parser("segments", help="List all available market segments")

    # status — show pipeline status
    subparsers.add_parser("status", help="Show current pipeline status")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    pipeline = Pipeline()

    if args.command == "run":
        pipeline.set_segment(getattr(args, "segment", "big-corp"))
        companies = args.companies or []
        if args.file:
            with open(args.file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        if "," in line:
                            parts = [p.strip() for p in line.split(",", 1)]
                            companies.append((parts[0], parts[1]))
                        else:
                            companies.append(line)
        if not companies:
            print("[ERROR] Provide company names or --file")
            run_parser.print_help()
            return
        pipeline.run_search(companies)

    elif args.command == "enrich":
        urls = args.linkedin or []
        if args.file:
            with open(args.file, "r", encoding="utf-8") as f:
                urls.extend(line.strip() for line in f if line.strip())
        if not urls:
            print("[ERROR] Provide LinkedIn URLs or --file")
            enrich_parser.print_help()
            return
        pipeline.enrich_linkedin(urls)

    elif args.command == "daily":
        pipeline.set_segment(getattr(args, "segment", "big-corp"))
        pipeline.run_daily()

    elif args.command == "segments":
        print_header("Market Segments")
        for key, seg in SEGMENTS.items():
            print(f"  {key:15s}  {seg['name']}")
            print(f"  {'':15s}  {seg['description']}")
            print(f"  {'':15s}  Sales cycle: {seg['sales_cycle']}")
            print(f"  {'':15s}  Companies file: {seg['companies_file']}")
            print()

    elif args.command == "status":
        pipeline.show_status()


if __name__ == "__main__":
    main()
