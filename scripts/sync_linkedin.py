#!/usr/bin/env python3
"""
Fetches experience data from LinkedIn and writes experience.json.

Authentication (set as GitHub Actions secrets):
  Recommended — LINKEDIN_LI_AT (session cookie, lasts ~1 year, no bot detection):
    1. Log into linkedin.com in Chrome
    2. DevTools → Application → Cookies → linkedin.com → copy "li_at" value
    3. Add as GitHub secret: LINKEDIN_LI_AT

  Fallback — LINKEDIN_EMAIL + LINKEDIN_PASSWORD
"""

import json
import os
import sys

try:
    from linkedin_api import Linkedin
except ImportError:
    print("ERROR: linkedin-api not installed.")
    sys.exit(1)

PROFILE_ID = "kailash-parshad"
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
    import re
    if not text:
        return ""
    return re.sub(r"\s+", " ", text).strip()


def connect():
    li_at = os.environ.get("LINKEDIN_LI_AT")
    if li_at:
        print("Authenticating via li_at cookie...")
        api = Linkedin("", "", authenticate=False)
        api.client.session.cookies.set("li_at", li_at, domain=".linkedin.com")
        api.client.session.headers.update({"csrf-token": "ajax:0"})
        return api

    email    = os.environ.get("LINKEDIN_EMAIL")
    password = os.environ.get("LINKEDIN_PASSWORD")
    if email and password:
        print("Authenticating via email/password...")
        return Linkedin(email, password)

    print("ERROR: No credentials. Set LINKEDIN_LI_AT or LINKEDIN_EMAIL + LINKEDIN_PASSWORD.")
    sys.exit(1)


def main():
    api = connect()

    print(f"Fetching profile: {PROFILE_ID}")
    profile   = api.get_profile(PROFILE_ID)
    positions = profile.get("experience", [])

    if not positions:
        print("No experience data returned. Check credentials and profile ID.")
        sys.exit(1)

    entries = []
    for pos in positions:
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
            "description": desc
        })

    if not entries:
        print("All positions were empty after parsing.")
        sys.exit(1)

    out_path = os.path.normpath(OUTPUT_FILE)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(entries, f, indent=2, ensure_ascii=False)

    print(f"Written {len(entries)} entries to {out_path}")


if __name__ == "__main__":
    main()
