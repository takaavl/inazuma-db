# INAZUMA — GitHub + Vercel + Turso Cloud

## Architecture

- **GitHub** stores the application code only.
- **Vercel** runs the FastAPI application.
- **Turso Cloud** stores the persistent SQLite-compatible production database.
- Local development can use the local `data/inazuma.sqlite3` file, or connect directly to the same Turso database through a private `.env` file.

Do not commit a local SQLite database, raw Tracker JSON, or secrets to GitHub.

## Unlisted access

The app emits `noindex` directives in HTML and `X-Robots-Tag` response headers. This asks search engines not to index the pages. It does **not** make the site private: anyone who gets the URL can visit it. Keep the URL off public profiles and do not link it from the previous dashboard.

## GitHub

From the `inazuma_dashboard` folder:

```bash
git init
git add .
git status
git commit -m "Initial INAZUMA dashboard"
git branch -M main
```

Connect the repository you created (currently named `inazuma-db`):

```bash
git remote add origin https://github.com/YOUR_USERNAME/inazuma-db.git
git push -u origin main
```

If Git says that `origin` already exists, use `git remote -v` to inspect it rather than adding another remote. Do not force-push.

## Turso Cloud

1. Create a **new, empty Turso database for Inazuma**. Do not reuse the previous dashboard's database.
2. Copy its database URL (`libsql://...`) and create an authentication token with read/write access.
3. Keep both values private. They are the credentials used by the server to access the database.

The app automatically creates the Inazuma schema and seeds the five confirmed players the first time it connects to an empty Turso database.

## Vercel

1. Import the `inazuma-db` GitHub repository into Vercel.
2. Keep Root Directory as `./`.
3. The Python entrypoint is declared in `pyproject.toml` as `main:app`; no custom Build Command or Output Directory is required.
4. Add these Environment Variables for **Production, Preview and Development** as appropriate:
   - `TURSO_DATABASE_URL` = the Inazuma database URL (`libsql://...`)
   - `TURSO_AUTH_TOKEN` = the Inazuma read/write auth token
   - `ADMIN_CODE` = your private admin code
   - `ADMIN_COOKIE_SECRET` = a long random secret string
5. Redeploy after adding or changing environment variables.
6. Verify `/health` returns `{"status":"ok","database":"turso"}` and then open the homepage.

Vercel's function filesystem is temporary, so the application uses Turso for persistent production data. A temporary SQLite fallback exists only to allow an initial deployment before the Turso variables are configured; do not use it for real match data.

## Local admin that writes to the production database

To make imports from your PC save directly to the same database used by Vercel:

1. Copy `.env.example` to `.env` in the project folder.
2. Put the same `TURSO_DATABASE_URL` and `TURSO_AUTH_TOKEN` values in `.env`.
3. Keep `.env` private; `.gitignore` excludes it.
4. Start the dashboard with `START_WINDOWS.bat` and use `http://127.0.0.1:8000/admin/`.

When those two Turso variables are present, local development uses Turso Cloud instead of the local SQLite file. Imports and future roster edits made locally are therefore saved directly to the production database; no database file needs to be committed or redeployed.

The hosted `/admin/` remains read-only. Use the local admin connected to Turso for data changes.

## Updating the website

- **Code or design change:** commit and push to GitHub; Vercel deploys automatically.
- **Match/event/player data change:** use the local admin while connected to Turso; the change is available on the hosted site immediately after the database write succeeds. No Git push is needed for data-only changes.

## Secrets and private data

- Never commit `.env`, Turso auth tokens, `data/admin_codes.txt`, raw Tracker JSON, or private database archives.
- The production database is separate from the old dashboard's database.
