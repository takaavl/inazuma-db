# INAZUMA foundation — initial project preparation

- Rebranded the independent app as INAZUMA.
- Replaced mauve/purple accents with dark charcoal and yellow/gold.
- Added noindex meta and X-Robots-Tag response headers for unlisted deployment.
- Created a clean independent SQLite schema with player roles/order, tournament tiers S/A/B/C and Career Highlights fields.
- Removed old roster-specific bulk import and private historical databases from this project copy.
- Preserved the official Tracker JSON import and scoreboard-cache recovery pipeline as the starting point.

## Turso Cloud deployment preparation

- Added the same proven Python `libsql` remote adapter used by the previous Vercel/Turso dashboard.
- Local SQLite remains the offline fallback; setting `TURSO_DATABASE_URL` and `TURSO_AUTH_TOKEN` switches the app to Turso Cloud.
- Added first-connect schema bootstrap and automatic seeding of the five confirmed Inazuma players.
- Added the Vercel `main:app` entrypoint and Python 3.13 project configuration.
- Local admin can write directly to the shared Turso database when `.env` is configured; hosted Vercel admin remains read-only.
- Local SQLite files and `.env` secrets are now excluded from Git.
- Added `/health` to report whether the app is using Turso or local SQLite.
