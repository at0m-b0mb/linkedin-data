#!/usr/bin/env python3
"""
Fetches experience data from LinkedIn's Voyager API and writes experience.json.

Required GitHub secrets:
  LINKEDIN_LI_AT      — main auth cookie  (li_at)
  LINKEDIN_JSESSIONID — CSRF cookie       (JSESSIONID)

How to get both cookies:
  1. Log into linkedin.com in your browser
  2. Open DevTools → Application → Cookies → https://www.linkedin.com
  3. Copy the value of "li_at"      → LINKEDIN_LI_AT secret
  4. Copy the value of "JSESSIONID" → LINKEDIN_JSESSIONID secret
     (it looks like: ajax:1234567890ABCDEF — copy WITHOUT surrounding quotes)
"""

import json
import os
import re
import sys

try:
    import requests
except ImportError:
    print("ERROR: requests not installed.")
    sys.exit(1)

PROFILE_ID  = "kailash-parshad"
OUTPUT_FILE = os.path.join(os.path.dirname(__file__), "..", "experience.json")

MONTHS = ["Jan","Feb","Mar","Apr","May","Jun",
          "Jul","Aug","Sep","Oct","Nov","Dec"]


def fmt_date(d):
    if not d:
        return "Present"
    return f"{MONTHS[d.get('month', 1) - 1]} {d.get('year', '')}"


def fmt_period(tp):
    start = fmt_date(tp.get("startDate"))
    end   = fmt_date(tp.get("endDate")) if tp.get("endDate") else "Present"
    return f"{start} \u2014 {end}"


def clean(text):
    if not text:
        return ""
    return re.sub(r"\s+", " ", text).strip()


def make_session(li_at, jsessionid):
    csrf = jsessionid.strip('"').strip("'")
    session = requests.Session()
    session.cookies.set("li_at",      li_at,       domain=".linkedin.com")
    session.cookies.set("JSESSIONID", f'"{csrf}"', domain=".linkedin.com")
    session.headers.update({
        "csrf-token":                 csrf,
        "x-restli-protocol-version": "2.0.0",
        "x-li-lang":                 "en_US",
        "user-agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
        "accept": "application/vnd.linkedin.normalized+json+2.1",
    })
    return session


def fetch_profile_view(session):
    """profileView returns the full profile including positionView."""
    url = (
        f"https://www.linkedin.com/voyager/api/identity/profiles"
        f"/{PROFILE_ID}/profileView"
    )
    res = session.get(url)
    if res.status_code == 401:
        print("ERROR: 401 — li_at or JSESSIONID expired. Re-copy from browser.")
        sys.exit(1)
    if res.status_code == 403:
        print("ERROR: 403 — CSRF check failed. Check LINKEDIN_JSESSIONID has no outer quotes.")
        sys.exit(1)
    if not res.ok:
        print(f"ERROR: LinkedIn returned HTTP {res.status_code}")
        print(res.text[:500])
        sys.exit(1)
    try:
        return res.json()
    except Exception:
        print("ERROR: Could not parse response as JSON.")
        print("First 500 chars:", res.text[:500])
        sys.exit(1)


def parse_entries(data):
    # profileView nests positions under positionView.elements
    position_view = data.get("positionView", {})
    elements = position_view.get("elements", [])

    # Fallback: some responses wrap under top-level elements
    if not elements:
        elements = data.get("elements", [])

    entries = []
    for pos in elements:
        title   = clean(pos.get("title", ""))
        company = clean(pos.get("companyName", ""))
        desc    = clean(pos.get("description", ""))
        date    = fmt_period(pos.get("timePeriod", {}))

        if not title or not company:
            continue

        entries.append({
            "date":        date,
            "title":       title,
            "company":     company,
            "description": desc,
        })

    return entries


def main():
    li_at      = os.environ.get("LINKEDIN_LI_AT", "").strip()
    jsessionid = os.environ.get("LINKEDIN_JSESSIONID", "").strip()

    if not li_at:
        print("ERROR: LINKEDIN_LI_AT secret is not set.")
        sys.exit(1)
    if not jsessionid:
        print("ERROR: LINKEDIN_JSESSIONID secret is not set.")
        sys.exit(1)

    print(f"Fetching profile view for: {PROFILE_ID}")
    session = make_session(li_at, jsessionid)
    data    = fetch_profile_view(session)
    entries = parse_entries(data)

    if not entries:
        print("No experience entries found in API response.")
        print("Raw keys:", list(data.keys()))
        sys.exit(1)

    out_path = os.path.normpath(OUTPUT_FILE)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(entries, f, indent=2, ensure_ascii=False)

    print(f"Written {len(entries)} entries to experience.json")


if __name__ == "__main__":
    main()
