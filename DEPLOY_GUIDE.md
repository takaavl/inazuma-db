# INAZUMA — GitHub + Vercel setup

## Unlisted access

The app emits `noindex` directives in HTML and `X-Robots-Tag` response headers. This asks search engines not to index the pages. It does **not** make the site private: anyone who gets the URL can visit it. Keep the URL off public profiles and do not link it from the previous dashboard.

## GitHub

From the `inazuma_dashboard` folder, after confirming the project files:

```bash
git init
git add .
git commit -m "Initial INAZUMA dashboard"
git branch -M main
```

Create a new empty GitHub repository named `inazuma-dashboard`, then connect it:

```bash
git remote add origin https://github.com/YOUR_USERNAME/inazuma-dashboard.git
git push -u origin main
```

Do not reuse the old dashboard repository.

## Vercel

1. Sign in to Vercel with GitHub.
2. Choose **Add New → Project** and import the new `inazuma-dashboard` repository.
3. Keep Root Directory as `./`; leave Build Command and Output Directory empty.
4. Deploy.
5. Add `ADMIN_CODE` as an Environment Variable and redeploy. Optionally add a long random `ADMIN_COOKIE_SECRET`.
6. Keep the generated URL unlinked and unadvertised.

Every push to `main` triggers a deployment.

## Updating match data

Import locally through `/admin/`, review the result, then run `PREPARE_DEPLOY_WINDOWS.bat` before committing the compact database. Raw Tracker exports are stored under `data/private_raw/` and ignored by Git.
