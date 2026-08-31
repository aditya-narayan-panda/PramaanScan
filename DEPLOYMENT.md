# Deploying PramaanScan

Stack: **GitHub** (source) -> **Supabase** (Postgres) -> **Render** (FastAPI backend) -> **Vercel** (React frontend).

Repo layout that deployment depends on — don't rename these two top-level folders,
the backend's `sys.path` wiring assumes they're siblings at the repo root:

```
pramaanscan/
├── backend_final/    # FastAPI app
├── PramaanScan_ML/   # ML models the backend imports (audio/image/video/doc forensics)
├── frontend/          # React + Vite app (renamed from pramaanscan-frontend/frontend — safe, JS-only)
├── render.yaml         # Render Blueprint
├── runtime.txt          # Python version pin for Render
└── .gitignore
```

---

## 1. Push to GitHub

```bash
cd pramaanscan
git init
git add .
git commit -m "Initial commit"
git branch -M main
gh repo create pramaanscan --private --source=. --push
# or, without the gh CLI: create an empty repo on github.com, then
#   git remote add origin https://github.com/<you>/pramaanscan.git
#   git push -u origin main
```

Repo size after cleanup is ~78 MB (models included), well under GitHub's limits — no Git LFS needed.

---

## 2. Supabase (Postgres database)

1. Create a project at supabase.com.
2. Project Settings -> Database -> Connection string -> copy the **Transaction pooler**
   URI (port `6543`) — it's the one designed for serverless/short-lived connections
   like a Render web service. It looks like:
   ```
   postgresql://postgres.xxxxxxxx:[YOUR-PASSWORD]@aws-0-<region>.pooler.supabase.com:6543/postgres
   ```
3. Swap in your real database password. This full string becomes `DATABASE_URL`.
4. You do **not** need to run any SQL by hand — `create_db.py` calls
   `Base.metadata.create_all()`, which creates all tables on first boot.
   (There's no Alembic/migrations setup here — fine for now, but worth adding
   once the schema starts changing after go-live.)

If you'd rather skip Supabase for a first deploy, Render's own managed Postgres
works identically — just paste *its* connection string as `DATABASE_URL` instead.

---

## 3. Render (backend)

**Option A — Blueprint (recommended):** New -> Blueprint -> point at your GitHub
repo. Render reads `render.yaml` and creates the service for you. You'll still
need to fill in the four `sync: false` variables in the dashboard afterward
(`DATABASE_URL`, `PUBLIC_BASE_URL`, `FRONTEND_BASE_URL`, `CORS_ORIGINS`) — see step 5.

**Option B — Manual Web Service:**
| Setting | Value |
|---|---|
| Runtime | Python 3 |
| Build Command | `pip install -r backend_final/requirements-backend.txt -r PramaanScan_ML/requirements.txt` |
| Start Command | `cd backend_final && python create_db.py && uvicorn app.main:app --host 0.0.0.0 --port $PORT` |
| Health Check Path | `/api/v1/health` |

**Plan/RAM — read this before picking Free/Starter:** the backend imports
TensorFlow, MediaPipe, OpenCV, and librosa for video/image/audio forensics.
Free and Starter instances are 512 MB RAM, which these libraries alone can
approach or exceed once a model is loaded. Start on **Standard (2 GB)**; watch
the memory graph after a real request hits `/api/v1/media/*`, and size up to
Pro if you see OOM restarts in the logs.

Also note: Render's free instances spin down after 15 minutes idle and take
~30-60s to wake on the next request — fine for a demo, less fine if you want
snappy first-load for reviewers.

---

## 4. Vercel (frontend)

1. New Project -> import the same GitHub repo.
2. Set **Root Directory** to `frontend` (this repo has multiple projects in one repo).
3. Framework preset: Vite (auto-detected). Build command `npm run build`,
   output directory `dist` (auto-filled).
4. Environment Variables -> add `VITE_API_BASE_URL` = your Render backend URL
   plus `/api/v1`, e.g. `https://pramaanscan-backend.onrender.com/api/v1`.
   (Vite bakes env vars in at build time — set this *before* the first deploy,
   and redeploy after changing it later.)
5. `frontend/vercel.json` is already set up to rewrite all paths to
   `index.html`, so React Router's client-side routes don't 404 on refresh.

---

## 5. Wire them together

Once you have both live URLs, go back to Render's environment variables and set:

| Variable | Value |
|---|---|
| `DATABASE_URL` | your Supabase connection string from step 2 |
| `PUBLIC_BASE_URL` | `https://pramaanscan-backend.onrender.com` (your Render URL) |
| `FRONTEND_BASE_URL` | `https://pramaanscan.vercel.app` (your Vercel URL) |
| `CORS_ORIGINS` | same Vercel URL(s), comma-separated, **no trailing slash** |

Redeploy the backend after saving. With `APP_ENV=production` the permissive
localhost CORS regex in `main.py` is disabled, so `CORS_ORIGINS` is the only
thing that decides who can call the API — double-check it matches your Vercel
domain exactly (including `www.` if you use it).

---

## 6. Before you call it done

- [ ] `JWT_SECRET` and `KEY_ENCRYPTION_SECRET` are long random values, not the
      `CHANGE_ME` defaults (Render's blueprint auto-generates these for you;
      set them by hand if deploying manually).
- [ ] The demo accounts in the root `README.md` (`admin@pramaanscan.gov.in` /
      `Admin@12345`, etc.) are seeded by `seed_db.py` with **fixed, public**
      passwords. Don't run `seed_db.py` against production, or if you do,
      change those passwords immediately — they're printed in your repo's
      README for anyone to read.
- [ ] Hit `https://<your-render-url>/api/v1/health` — should return
      `{"status":"ok", ...}`.
- [ ] Upload a test file through the deployed frontend and confirm a real
      verification result comes back (this exercises the full DB + ML path).
- [ ] Custom domain (optional): both Render and Vercel support adding one
      under their respective dashboard's Settings -> Domains, once you're
      ready to move off the `*.onrender.com` / `*.vercel.app` subdomains.
