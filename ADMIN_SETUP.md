# Admin access

The public dashboard does not show Admin or Data Health.

## Local

On the first `START_WINDOWS.bat` launch, choose an admin code. It is stored in `data/admin_codes.txt`, which is ignored by Git.

Then open `http://127.0.0.1:8000/admin/`.

## Local admin connected to Turso Cloud

Copy `.env.example` to `.env` and fill in:

- `TURSO_DATABASE_URL`
- `TURSO_AUTH_TOKEN`

With those variables present, the local dashboard reads and writes the persistent Inazuma Turso database. This is the recommended way to import matches and manage production data.

## Vercel

In Vercel → Project → Settings → Environment Variables, configure:

- `TURSO_DATABASE_URL`
- `TURSO_AUTH_TOKEN`
- `ADMIN_CODE`
- `ADMIN_COOKIE_SECRET` (long random string)

Redeploy after saving the variables. The hosted admin stays read-only; use the local dashboard connected to Turso for data changes.
