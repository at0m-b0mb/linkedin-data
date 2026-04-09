#!/usr/bin/env python3
"""
Fetches experience data from LinkedIn and writes experience.json.

Required GitHub secrets:
  LINKEDIN_EMAIL    — your LinkedIn login email
  LINKEDIN_PASSWORD — your LinkedIn login password

The linkedin-api library handles authentication and uses current endpoints.
"""

import json
import os
import re
import sys

try:
    from linkedin_api import Linkedin
except ImportError:
    print("ERROR: linkedin-api not installed. Run: pip install linkedin-api")
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


def main():
    email    = os.environ.get("LINKEDIN_EMAIL", "").strip()
    password = os.environ.get("LINKEDIN_PASSWORD", "").strip()

    if not email or not password:
        print("ERROR: LINKEDIN_EMAIL and LINKEDIN_PASSWORD secrets must be set.")
        sys.exit(1)

    print("Authenticating with LinkedIn...")
    try:
        api = Linkedin(email, password)
    except Exception as e:
        print(f"ERROR: Authentication failed — {e}")
        print("Check your email/password secrets are correct.")
        sys.exit(1)

    print(f"Fetching profile: {PROFILE_ID}")
    try:
        profile = api.get_profile(PROFILE_ID)
    except Exception as e:
        print(f"ERROR: Could not fetch profile — {e}")
        sys.exit(1)

    positions = profile.get("experience", [])
    if not positions:
        print("No experience entries returned.")
        print("Profile keys found:", list(profile.keys()))
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
            "description": desc,
        })

    if not entries:
        print("All positions were empty after parsing.")
        sys.exit(1)

    out_path = os.path.normpath(OUTPUT_FILE)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(entries, f, indent=2, ensure_ascii=False)

    print(f"Written {len(entries)} entries to experience.json")


if __name__ == "__main__":
    main()
