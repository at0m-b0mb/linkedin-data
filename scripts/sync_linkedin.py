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


def fetch_positions(li_at, jsessionid):
    # Strip quotes that some browsers include around JSESSIONID
    csrf = jsessionid.strip('"').strip("'")

    session = requests.Session()
    session.cookies.set("li_at",      li_at,    domain=".linkedin.com")
    session.cookies.set("JSESSIONID", f'"{csrf}"', domain=".linkedin.com")

    session.headers.update({
        "csrf-token":                  csrf,
        "x-restli-protocol-version":  "2.0.0",
        "x-li-lang":                  "en_US",
        "x-li-track":                 '{"clientVersion":"1.13.9"}',
        "user-agent":                  (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/123.0.0.0 Safari/537.36"
        ),
        "accept":                      "application/vnd.linkedin.normalized+json+2.1",
    })

    url = (
        f"https://www.linkedin.com/voyager/api/identity/profiles"
        f"/{PROFILE_ID}/positions?count=100&start=0"
    )
    res = session.get(url)

    if res.status_code == 401:
        print("ERROR: 401 Unauthorized — your li_at or JSESSIONID may have expired. Re-copy them from the browser.")
        sys.exit(1)
    if res.status_code == 403:
        print("ERROR: 403 Forbidden — CSRF check failed. Make sure LINKEDIN_JSESSIONID is set correctly (no outer quotes).")
        sys.exit(1)
    if not res.ok:
        print(f"ERROR: LinkedIn returned HTTP {res.status_code}")
        print(res.text[:500])
        sys.exit(1)

    try:
        return res.json()
    except Exception:
        print("ERROR: Could not parse LinkedIn response as JSON.")
        print("First 500 chars:", res.text[:500])
        sys.exit(1)


def parse_entries(data):
    # Voyager API wraps results under 'elements' or a nested included list
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

    print(f"Fetching positions for: {PROFILE_ID}")
    data    = fetch_positions(li_at, jsessionid)
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
