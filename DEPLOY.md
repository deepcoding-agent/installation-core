# PrepPilot — Production Deployment Guide

End-to-end manual for taking PrepPilot from a clean checkout to a live
production deployment.

> **Companion docs:**
> - [`SETUP-CICD.md`](SETUP-CICD.md) — CI/CD pipeline secrets & toggles
> - [`../docs/SPRINT_PLAN.md`](../docs/SPRINT_PLAN.md) — Sprint 7 & 8 acceptance criteria
> - [`README.md`](README.md) — local-only Docker Compose orchestration

The four repos deploy to different platforms — **set up each one in order**.
Skipping ahead breaks downstream steps.

```
┌─────────────────────┐      ┌──────────────────────┐
│  web-app  (Vercel)  │ ──→  │ ml-datascience (Fly) │
│  Next.js standalone │      │  FastAPI + 417 hdlrs │
└──────────┬──────────┘      └──────────┬───────────┘
           │ NextAuth                   │ joblib models
           ▼                            ▼
   ┌──────────────────┐      ┌──────────────────────┐
   │ MongoDB Atlas    │      │ Fly persistent volume│
   │ (preppilot db)   │      │ (preppilot_models)   │
   └──────────────────┘      └──────────────────────┘
```

---

## 0. What's already prepared for you ✅

Sprint 7 + 8 prep is complete in the code:

| Item | Where | What |
|------|-------|------|
| Multi-stage prod Dockerfiles | `web-app/Dockerfile`, `ml-datascience/Dockerfile` | `next start` + non-root user; `uvicorn` no-reload + non-root user |
| Dev Dockerfiles preserved | `*/Dockerfile.dev` | docker-compose still works for local dev |
| Next.js standalone output | `web-app/next.config.ts` | `output: "standalone"` for any self-hosted Docker deploy |
| CORS lockdown | `api/main.py` | `FRONTEND_ORIGIN` env (comma-separated allowlist) |
| Rate limiting | `api/routes/chat.py`, `api/routes/train.py` | slowapi: /chat 60/min, /train 6/min, default 240/min |
| Sandbox hardening | `api/sandbox.py` | Import blocklist + 30s wall-clock timeout |
| Structured errors | `api/main.py` | All errors return `{error:{code,message,request_id}}` |
| Fly volume mount | `ml-datascience/fly.toml` | `/app/models` mount; `MODELS_DIR=/app/models` |
| Prisma → MongoDB | `web-app/prisma/schema.prisma` | ObjectId IDs, `provider = "mongodb"` |
| SQLite kept as backup | `web-app/prisma/schema.sqlite.prisma` | Reference only |

What you still have to do yourself: **provision the cloud accounts and wire the secrets**. That's what the rest of this doc covers.

---

## 1. Prerequisites

Install once:

```bash
brew install gh flyctl                  # GitHub + Fly CLI (macOS)
npm i -g vercel@latest                  # Vercel CLI
```

You also need accounts on:

1. **GitHub** — already have it (you push code here)
2. **Vercel** — https://vercel.com/signup (free Hobby tier is fine)
3. **Fly.io** — https://fly.io/app/sign-up (free tier covers 1×shared-cpu-1x)
4. **MongoDB Atlas** — https://account.mongodb.com/account/register (free M0 cluster)
5. **Google Cloud Console** — for OAuth credentials

---

## 2. Provision external resources

### 2.1 MongoDB Atlas — create the cluster

1. Atlas → **Build a Database** → free **M0** tier → region nearest your Fly region (Singapore for `sin`)
2. **Database Access** → add user `preppilot` with random 20-char password → role **readWriteAnyDatabase**
3. **Network Access** → add IP `0.0.0.0/0` (or restrict to Vercel egress IPs — see [vercel.com/guides/how-to-allowlist-deployment-ip-address](https://vercel.com/guides/how-to-allowlist-deployment-ip-address))
4. **Connect** → "Drivers" → copy the connection string:
   ```
   mongodb+srv://preppilot:<password>@cluster0.xxxxx.mongodb.net/preppilot?retryWrites=true&w=majority
   ```
5. Replace `<password>` with the user's real password. **Save this — it's `DATABASE_URL` in step 4.4.**

### 2.2 Google OAuth — create the client

1. https://console.cloud.google.com → **APIs & Services → Credentials**
2. **Create Credentials → OAuth client ID → Web application**
3. **Authorised JavaScript origins**:
   - `http://localhost:3000`
   - `https://your-domain.vercel.app` (you'll know this URL after step 3.3)
4. **Authorised redirect URIs**:
   - `http://localhost:3000/api/auth/callback/google`
   - `https://your-domain.vercel.app/api/auth/callback/google`
5. Save the **Client ID** and **Client Secret**.

### 2.3 Generate NextAuth secret

```bash
openssl rand -hex 32
```

Save the output. This is `AUTH_SECRET` in step 4.4.

---

## 3. Deploy the backend (Render)

Render is the recommended backend host — it reads the existing `Dockerfile` and `render.yaml` Blueprint with no CLI needed.

### 3.1 Push render.yaml to GitHub

The `ml-datascience/render.yaml` Blueprint is already in the repo. Just make sure it's on the branch you'll deploy from (e.g. `main`):

```bash
cd ml-datascience
git add render.yaml
git commit -m "chore: add render blueprint for backend deploy"
git push origin main
```

### 3.2 Create the Blueprint on Render

1. Open https://dashboard.render.com → **New → Blueprint**
2. **Connect** your GitHub account if you haven't already, then pick the `ml-datascience` repository
3. Render parses `render.yaml` and shows a preview — confirm:
   - Service name: `preppilot-backend`
   - Plan: `Starter` ($7/mo — 512MB RAM, always-on, persistent disk)
   - Region: `Singapore`
4. Click **Apply** — this creates the service but does NOT start it yet (it's waiting for env vars)

### 3.3 Set the three secrets

In the Render dashboard → `preppilot-backend` service → **Environment** tab, fill in the three keys marked `sync: false`:

| Key | Value |
|-----|-------|
| `OPENAI_API_KEY` | `sk-proj-…` (from your OpenAI dashboard) |
| `ANTHROPIC_API_KEY` | `sk-ant-…` (optional, only if you'll use Claude) |
| `FRONTEND_ORIGIN` | `https://preppilot.onrender.com` placeholder for now — update in §4.3 if Vercel gives a different URL |

Click **Save Changes** — Render auto-deploys.

### 3.4 Wait for the first deploy (~5-7 min)

Watch the build log in the dashboard. When the status badge turns **Live**:

```bash
curl https://preppilot-backend.onrender.com/health
# → {"status":"ok"}
```

**Save the URL** — it's `ML_BACKEND_URL` in §4.4.

> If the build OOMs on the Starter plan (xgboost + lightgbm + optuna can be heavy
> to import in 512MB), bump it: dashboard → Settings → Instance Type → **Standard** ($25/mo, 2GB).

### 3.5 GitHub auto-deploy is already wired

`autoDeploy: true` in `render.yaml` means every push to the connected branch triggers a redeploy. No GitHub secrets needed — Render watches the repo via its GitHub app integration.

### Appendix A — If you prefer Fly.io instead

The previous Fly.io setup is kept in `fly.toml` for reference. The full Fly path is:

```bash
cd ml-datascience
flyctl auth login
flyctl launch --no-deploy --copy-config --name preppilot-backend --region sin
flyctl volumes create preppilot_models --region sin --size 3
flyctl secrets set OPENAI_API_KEY="..." ANTHROPIC_API_KEY="..." FRONTEND_ORIGIN="..."
flyctl deploy
```

GitHub Actions deploy (already in `.github/workflows/deploy.yml`):

```bash
flyctl tokens create deploy -x 999999h
gh secret set FLY_API_TOKEN -b "<token>"
gh variable set FLY_DEPLOY_ENABLED -b "true"
```

Common gotcha: the 1 GB Starter machine can OOM during ML library import — use `flyctl scale memory 2048` to bump to 2 GB.

---

## 4. Deploy the frontend (Vercel)

### 4.1 Link the project

```bash
cd web-app
vercel link
# Pick your team/account, accept the suggested project name "preppilot"
cat .vercel/project.json   # note orgId and projectId
```

### 4.2 Generate the Vercel API token

https://vercel.com/account/tokens → create token scoped to your team.

### 4.3 First Vercel deploy (one-time, to claim a URL)

```bash
vercel --prod
```

After it finishes you'll get the URL (e.g. `https://preppilot.vercel.app`). Go back to:

1. **Google OAuth** (§2.2) — add this URL to authorised origins + redirect URIs.
2. **Fly secrets** (§3.3) — if it differs from your placeholder, rerun:
   ```bash
   flyctl secrets set FRONTEND_ORIGIN="https://preppilot.vercel.app"
   ```

### 4.4 Set Vercel environment variables

Vercel dashboard → Project → **Settings → Environment Variables** → add for **Production**:

| Name | Value |
|------|-------|
| `GOOGLE_CLIENT_ID` | from §2.2 |
| `GOOGLE_CLIENT_SECRET` | from §2.2 |
| `AUTH_SECRET` | from §2.3 |
| `NEXTAUTH_URL` | `https://preppilot.vercel.app` |
| `DATABASE_URL` | the MongoDB Atlas SRV string from §2.1 |
| `MONGODB_URI` | same as `DATABASE_URL` |
| `ML_BACKEND_URL` | `https://preppilot-backend.fly.dev` from §3.4 |

### 4.5 GitHub secrets + variable for web-app repo

```bash
cd web-app
gh secret set VERCEL_TOKEN      -b "<token from §4.2>"
gh secret set VERCEL_ORG_ID     -b "<orgId from .vercel/project.json>"
gh secret set VERCEL_PROJECT_ID -b "<projectId from .vercel/project.json>"
gh variable set VERCEL_DEPLOY_ENABLED -b "true"
```

### 4.6 Push to redeploy via CI

```bash
git push origin main
gh run watch
```

GitHub Actions runs CI, then deploys. Visit the Vercel URL → should land on the login page.

---

## 5. End-to-end sanity check

| Step | Expected |
|------|----------|
| `curl https://preppilot-backend.fly.dev/health` | `{"status":"ok"}` |
| Visit `https://preppilot.vercel.app` | Landing page renders |
| Click **Sign in with Google** | OAuth flow completes, redirects to /chatpage |
| Upload `housing.csv` from `docs/element/` | Dataset shows in DatasetPicker |
| Send `/insights` | AI Insights Report card appears within ~10s |
| Send `/train` (on a numeric dataset with target) | TrainResultCard appears within ~2 min, `.joblib` download works |

If any step fails:

```bash
flyctl logs                    # backend logs (last hour)
vercel logs <deployment-url>   # frontend logs
```

---

## 6. Rollback

| Target | Command |
|--------|---------|
| Vercel | Dashboard → Deployments → pick previous → **Promote to Production**, or `vercel rollback <url>` |
| Fly    | `flyctl releases list` → `flyctl releases rollback <version>` |

Always rollback the *frontend* first if Mongo schema is incompatible; the
backend doesn't talk to Mongo.

---

## 7. Cost estimate (free-tier baseline)

| Service | Free allowance | Likely usage | Overage trigger |
|---------|----------------|--------------|-----------------|
| Vercel Hobby | 100 GB bandwidth/mo, 100 builds/day | well under | only if you go public |
| Fly | 1× shared-cpu-1x always-on, 3 GB volume, 160 GB egress | well under (scale-to-zero) | only with sustained traffic |
| MongoDB Atlas M0 | 512 MB storage | ~5 MB per dataset, plenty | dataset library grows past ~500 MB |
| OpenAI gpt-4o-mini | pay-per-token | ~$0.15 / 1M input, ~$0.60 / 1M output | bulk chat usage |
| Anthropic Claude | pay-per-token | only if you switch the LLM | bulk chat usage |

**Hardest gate is OpenAI/Anthropic** — set a monthly cap in the OpenAI dashboard
(Usage limits → Hard limit). The rate limits in `chat.py` already cap requests/IP.

---

## 8. Where the wired-up env vars live (cheat sheet)

```
backend  (Fly secrets — set via flyctl secrets set)
  OPENAI_API_KEY        ─→ api/llm.py
  ANTHROPIC_API_KEY     ─→ api/llm.py
  FRONTEND_ORIGIN       ─→ api/main.py  CORS allowlist
  MODELS_DIR=/app/models ─ Dockerfile + fly.toml (set, not secret)

frontend (Vercel env vars — set in dashboard)
  GOOGLE_CLIENT_ID      ─→ src/auth.ts
  GOOGLE_CLIENT_SECRET  ─→ src/auth.ts
  AUTH_SECRET           ─→ next-auth
  NEXTAUTH_URL          ─→ next-auth (redirect callbacks)
  DATABASE_URL          ─→ prisma/schema.prisma  (MongoDB Atlas)
  MONGODB_URI           ─→ src/lib/prisma.ts
  ML_BACKEND_URL        ─→ next.js api proxies

GitHub (per-repo)
  web-app:        VERCEL_TOKEN, VERCEL_ORG_ID, VERCEL_PROJECT_ID  +  var VERCEL_DEPLOY_ENABLED=true
  ml-datascience: FLY_API_TOKEN                                    +  var FLY_DEPLOY_ENABLED=true
```

---

## 9. Order-of-operations TL;DR

1. Provision: Atlas cluster → Google OAuth → AUTH_SECRET
2. Backend first: `flyctl launch --no-deploy`, create volume, set secrets, `flyctl deploy`
3. Frontend: `vercel link`, `vercel --prod` (to get URL), update OAuth + Fly's FRONTEND_ORIGIN
4. Set Vercel env vars in dashboard
5. Wire GitHub secrets + flip `*_DEPLOY_ENABLED=true` in both repos
6. `git push origin main` → CI deploys
7. Sanity-test the live URLs against the checklist in §5
