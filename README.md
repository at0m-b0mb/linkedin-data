# linkedin-data

Automatically fetches LinkedIn experience data and stores it as `experience.json`.

## How it works

A GitHub Actions workflow (`sync.yml`) runs every Monday at 08:00 UTC (and can be triggered manually). It:

1. Installs [`linkedin-api`](https://github.com/tomquirk/linkedin-api)
2. Authenticates with your LinkedIn account using email + password
3. Fetches your public profile's experience section
4. Writes the result to `experience.json` and commits it back to `main`

## Setup

### 1. Add GitHub Secrets

Go to your repository → **Settings** → **Secrets and variables** → **Actions** → **New repository secret**, and add:

| Secret name         | Value                          |
|---------------------|--------------------------------|
| `LINKEDIN_EMAIL`    | Your LinkedIn login email      |
| `LINKEDIN_PASSWORD` | Your LinkedIn login password   |

### 2. Run the workflow

After the secrets are set, trigger a sync from the **Actions** tab → **Sync LinkedIn Experience** → **Run workflow**.

## Local development

```bash
pip install -r requirements.txt
export LINKEDIN_EMAIL="you@example.com"
export LINKEDIN_PASSWORD="yourpassword"
python scripts/sync_linkedin.py
```

## Output

`experience.json` — an array of experience entries:

```json
[
  {
    "date": "Jan 2025 — Present",
    "title": "Job Title",
    "company": "Company Name",
    "description": "Role description."
  }
]
```

## Notes

- LinkedIn may occasionally challenge logins with a CAPTCHA or verification email. If authentication fails, try logging in manually once, then re-run the workflow.
- The profile ID to fetch is set at the top of `scripts/sync_linkedin.py` (`PROFILE_ID`). Change it to your own LinkedIn public profile URL slug.
