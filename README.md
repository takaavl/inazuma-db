# INAZUMA — Competitive Performance Dashboard

A standalone Valorant team analytics dashboard for official matches, player performance, maps, compositions, tournaments and curated career highlights.

## Identity and access

- Brand and team: **INAZUMA**
- Visual direction: **dark charcoal + yellow/gold**
- Deployment intent: **unlisted** — pages send `noindex` directives to crawlers. This is not authentication: anyone with the URL can open the site.
- Independent production database on Turso Cloud. No previous team's match history, aliases or Tracker exports are included.

## Run locally on Windows

Double-click `START_WINDOWS.bat`, or run:

```bash
py -m pip install -r requirements.txt
py run.py
```

Then open `http://127.0.0.1:8000`. The first launch asks you to choose a local admin code.

Without Turso variables, local development uses `data/inazuma.sqlite3`.
To use the same persistent database as Vercel, copy `.env.example` to `.env` and set `TURSO_DATABASE_URL` and `TURSO_AUTH_TOKEN`. Keep `.env` private; it is ignored by Git.

## Current foundation

- Official match and map analytics based on the previous dashboard's stable import and cache pipeline.
- Initial roster: Takaa (Duelist), Duke (Recon), TempoKD (Duelist), LJPH (IGL / Controller) and Lugia (Sentinel).
- Tournament tiers S / A / B / C stored on events; matches inherit their tournament tier.
- Career Highlights page and curated highlight fields on series.
- Local admin can write directly to Turso when `.env` contains the production credentials. Hosted Vercel admin remains read-only.
- `noindex` meta and response headers for the unlisted deployment.

## Storage model

- **Local fallback:** `data/inazuma.sqlite3` for offline/local testing.
- **Production:** Turso Cloud. Match data and raw Tracker JSON are stored in the remote SQLite-compatible database.
- **GitHub:** source code only. No database file, raw Tracker JSON or secrets are committed.

## Deployment

See `DEPLOY_GUIDE.md` for the GitHub + Vercel + Turso setup and the local-admin workflow.
