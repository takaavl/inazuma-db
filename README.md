# INAZUMA — Competitive Performance Dashboard

A standalone Valorant team analytics dashboard for official matches, player performance, maps, compositions, tournaments and curated career highlights.

## Identity and access

- Brand: **INAZUMA**
- Visual direction: **dark charcoal + yellow/gold**
- Deployment intent: **unlisted** — pages send `noindex` directives to crawlers. This is not authentication: anyone with the URL can open the site.
- The project has its own SQLite database, seeded with Inazuma's confirmed starting five. No previous team's match history, aliases or Tracker exports are included.

## Run locally on Windows

Double-click `START_WINDOWS.bat`, or run:

```bash
py -m pip install -r requirements.txt
py scripts/init_database.py
py run.py
```

Then open `http://127.0.0.1:8000`. The first launch asks you to choose a local admin code.

## Current foundation

- Official match and map analytics based on the previous dashboard's stable import and cache pipeline.
- Independent database at `data/inazuma.sqlite3`.
- Initial roster cards and profile pages for Takaa (Duelist), Duke (Recon), TempoKD (Duelist), LJPH (IGL / Controller) and Lugia (Sentinel).
- Player cards show roster roles immediately; match statistics appear when official match data is imported.
- Editable roster fields are prepared in the schema (`role`, `display_order`, `roster_status`); the admin editing screen is a later implementation step.
- Tournament tiers S / A / B / C stored on events; matches inherit their tournament tier.
  - **S · Elite:** VCT, VCT Open Qualifiers and top-level competition.
  - **A · High Competitive:** VUKC, Premier Contender / Invite and comparable structured events.
  - **B · Competitive:** Tier 3 and regional circuits.
  - **C · Community:** smaller community tournaments.
- Career Highlights page and curated highlight fields on series; new series can be pinned during import.
- Local admin import; hosted Vercel admin remains read-only because bundled SQLite is not a durable write database.
- `noindex` meta and response headers for the unlisted deployment.

## Private data

- `data/inazuma.sqlite3` is the compact database used by the site and may be committed once populated.
- `data/private_full.sqlite3` and `data/private_raw/` are local-only archives and are ignored by Git.
- Never commit raw Tracker JSON or private source archives.

## Next setup steps

1. Complete the roster admin screen, aliases and player profile refinements.
2. Add statistics filters by tournament tier and refine Career Highlights.
3. Create the new GitHub repository and Vercel project together, step by step.
4. Import official match JSON and curate Career Highlights.

See `DEPLOY_GUIDE.md` for deployment.
