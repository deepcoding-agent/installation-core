# CI/CD Setup Checklist

This guide gets all four PrepPilot repos into a green CI + ready-to-deploy state.

The four repos are independent — set each one up separately. Run all checks
locally first with `npm run …` / `pytest`, then push and confirm GitHub Actions
goes green before flipping the deploy toggles.

---

## 0. Prerequisites

| Tool | Why | Install |
|------|-----|---------|
| GitHub CLI (`gh`) | Manage secrets per repo | `brew install gh` |
| Vercel CLI       | One-time link to Vercel project | `npm i -g vercel@latest` |
| Fly CLI (`flyctl`) | Bootstrap and deploy the backend | `brew install flyctl` |
| `openssl`        | Generate `AUTH_SECRET` | preinstalled |
| Docker           | Run the docker-compose CI fallback locally | Docker Desktop |

---

## 1. Repo: `web-app` (Next.js → Vercel)

### 1.1 Install new dev dependencies

```bash
cd web-app
npm install --save-dev vitest @vitest/coverage-v8
```

### 1.2 Verify CI passes locally

```bash
npm run typecheck
npm run test:coverage
npm run build
```

### 1.3 Bootstrap the Vercel project (once)

```bash
cd web-app
vercel link        # answer the prompts; creates .vercel/project.json
vercel env pull    # pulls existing env into .env.local (optional)
```

The link writes `.vercel/project.json` containing `orgId` and `projectId`.
Read those values:

```bash
cat .vercel/project.json
```

### 1.4 Add GitHub secrets (web-app repo)

In `Settings → Secrets and variables → Actions → New repository secret`:

| Name | Where to get it |
|------|-----------------|
| `VERCEL_TOKEN` | https://vercel.com/account/tokens — create a token, scoped to your team |
| `VERCEL_ORG_ID` | from `.vercel/project.json` → `orgId` |
| `VERCEL_PROJECT_ID` | from `.vercel/project.json` → `projectId` |

### 1.5 Add GitHub variable (toggles deploy)

In `Settings → Secrets and variables → Actions → Variables`:

| Name | Value | Purpose |
|------|-------|---------|
| `VERCEL_DEPLOY_ENABLED` | `true` | Set to `true` only after the three secrets above exist |

### 1.6 Set production env vars in Vercel

In the Vercel dashboard → Project → Settings → Environment Variables, set
each value from `.env.example` for the **Production** environment:

```
GOOGLE_CLIENT_ID
GOOGLE_CLIENT_SECRET
AUTH_SECRET                # openssl rand -hex 32
NEXTAUTH_URL               # https://your-domain.vercel.app  (or custom)
DATABASE_URL               # MongoDB Atlas URI for prod
MONGODB_URI                # same as DATABASE_URL
ML_BACKEND_URL             # https://preppilot-backend.fly.dev (from step 2)
```

### 1.7 Push and verify

```bash
git push origin main
gh run watch
```

CI must be green and the Vercel deploy job must produce a live URL.

---

## 2. Repo: `ml-datascience` (FastAPI → Fly.io)

### 2.1 Install dev deps locally

```bash
cd ml-datascience
source .venv/bin/activate
pip install -r requirements-dev.txt
```

### 2.2 Verify CI passes locally

```bash
pytest
ruff check api/
python -c "from api.main import app; print('OK')"
bandit -r api/ -ll -ii
```

### 2.3 Bootstrap the Fly app (once)

```bash
cd ml-datascience
flyctl auth login
flyctl launch --no-deploy --copy-config --name preppilot-backend --region sin
```

Confirm the app name in `fly.toml` matches what you chose. Then set the
required production secrets:

```bash
flyctl secrets set \
  OPENAI_API_KEY=sk-... \
  ANTHROPIC_API_KEY=sk-ant-...
```

### 2.4 Get the Fly API token for GitHub

```bash
flyctl tokens create deploy -x 999999h
```

Copy the token (starts with `FlyV1 …`).

### 2.5 Add GitHub secret + variable (ml-datascience repo)

Secret:

| Name | Value |
|------|-------|
| `FLY_API_TOKEN` | the token from step 2.4 |

Variable (`Settings → Secrets and variables → Actions → Variables`):

| Name | Value |
|------|-------|
| `FLY_DEPLOY_ENABLED` | `true` |

### 2.6 First deploy

```bash
flyctl deploy
```

After it succeeds, the next push to `main` will deploy via GitHub Actions.
Confirm `https://preppilot-backend.fly.dev/health` returns 200, then plug
that URL into the web-app's `ML_BACKEND_URL` (step 1.6).

---

## 3. Repo: `installation-core` (Docker Compose orchestration)

No deploy — CI just validates the compose file, lints scripts, and scans
for leaked secrets. Push and verify CI is green:

```bash
cd installation-core
git push origin main
gh run watch
```

---

## 4. Repo: `docs` (Markdown only)

CI runs markdownlint and a broken-link check, both non-blocking. Nothing
else to do.

---

## 5. Coverage gates (Sprint 6 todo)

Both `web-app` and `ml-datascience` ship with coverage thresholds set to
**0%** today, with a single smoke test each. This is intentional — CI must
be green *before* deploy can happen. Sprint 6 will:

1. Write real unit + integration tests.
2. Ramp `vitest.config.ts → thresholds` to 80% in `web-app`.
3. Ramp `pyproject.toml → tool.coverage.report.fail_under` to 80% in `ml-datascience`.

Until then the only contract is "tests must pass, even if there's only one".

---

## 6. Docker-compose CI fallback

Each app repo has `ci/docker-compose.ci.yml`. Run any CI step on any host:

```bash
# web-app
docker compose -f web-app/ci/docker-compose.ci.yml run --rm typecheck
docker compose -f web-app/ci/docker-compose.ci.yml run --rm test

# ml-datascience
docker compose -f ml-datascience/ci/docker-compose.ci.yml run --rm imports
docker compose -f ml-datascience/ci/docker-compose.ci.yml run --rm test
```

Useful when a runner doesn't have Node or Python preinstalled, or for
mirroring the pipeline outside GitHub Actions (GitLab, self-hosted, etc.).

---

## 7. Rollback

| Target | Command |
|--------|---------|
| Vercel | `vercel rollback <url>` or pick a prior deploy in the dashboard |
| Fly    | `flyctl releases list` → `flyctl releases rollback <version>` |

---

## 8. Quick verification checklist

- [ ] `gh secret list` shows the three Vercel secrets in `web-app`
- [ ] `gh secret list` shows `FLY_API_TOKEN` in `ml-datascience`
- [ ] `gh variable list` shows `VERCEL_DEPLOY_ENABLED=true` and `FLY_DEPLOY_ENABLED=true`
- [ ] `https://preppilot-backend.fly.dev/health` returns 200
- [ ] Vercel deploy URL loads the chat page
- [ ] One end-to-end chat message succeeds against the deployed backend
