# installation-core — DS-Agent Setup & Launcher

One repo to clone. One command to run. Everything else is automatic.

---

## Quick Start

```bash
git clone https://github.com/deepcoding-agent/installation-core.git installation-core
cd installation-core
python run.py --docker-build
```

That's it. `run.py` will:
1. Clone `web-app` and `ml-datascience` automatically if missing
2. Check Docker is installed and running
3. Verify all `.env` files are filled in
4. Build Docker images and start both services

---

## Prerequisites

| Tool | Minimum | Install |
|------|---------|---------|
| Python | 3.10+ | [python.org](https://python.org) · Mac: `brew install python` |
| Git | any | [git-scm.com](https://git-scm.com) · Mac: `brew install git` |
| Docker Desktop | latest | [docker.com](https://docker.com) *(Docker mode only)* |
| Node.js | 18+ | [nodejs.org](https://nodejs.org) *(Local mode only)* |

---

## First-Time Setup

### Step 1 — Clone this repo

```bash
git clone https://github.com/deepcoding-agent/installation-core.git installation-core
```

> `web-app` and `ml-datascience` will be cloned automatically on first run. No need to clone them manually.

---

### Step 2 — Configure the ML backend

The first run will create `../ml-datascience/api/.env` from the example file automatically. Open it and fill in:

```env
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini
```

Get your key at [platform.openai.com/api-keys](https://platform.openai.com/api-keys).

---

### Step 3 — Configure the web app

The first run will create `../web-app/.env.local` from the example file automatically. Open it and fill in:

```env
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret
AUTH_SECRET=your-random-secret
NEXTAUTH_URL=http://localhost:3000
ML_BACKEND_URL=http://localhost:8000
DATABASE_URL="file:./prisma/dev.db"
```

See [Google OAuth Setup](#google-oauth-setup) below for how to get the Google credentials.

Generate `AUTH_SECRET`:
```bash
openssl rand -hex 32
```

---

### Step 4 — Run

```bash
python run.py --docker-build
```

Open the app at **http://localhost:3000**

---

## Commands

```bash
# ── Docker (recommended) ───────────────────────────────────────────
python run.py --docker-build   # first run, or after pulling new code
python run.py --docker         # subsequent runs (faster, no rebuild)
python run.py --docker-down    # stop all containers

# ── Local / no Docker ──────────────────────────────────────────────
python run.py                  # install deps + start
python run.py --install        # install deps only
python run.py --start          # start only (deps already installed)
```

---

## Services

| Service | URL |
|---------|-----|
| Web App | http://localhost:3000 |
| ML Backend | http://localhost:8000 |
| API Docs (Swagger) | http://localhost:8000/docs |

---

## Google OAuth Setup

1. Go to [console.cloud.google.com](https://console.cloud.google.com)
2. Create a project → **APIs & Services → Credentials**
3. Click **Create Credentials → OAuth 2.0 Client ID**
4. Application type: **Web application**
5. Under **Authorized redirect URIs** add:
   ```
   http://localhost:3000/api/auth/callback/google
   ```
6. Copy the **Client ID** and **Client Secret** into `web-app/.env.local`

---

## Project Structure

```
(parent folder)/
├── installation-core/    ← clone this first — controls everything
├── web-app/              ← cloned automatically by run.py
└── ml-datascience/       ← cloned automatically by run.py
```

Each folder is its own git repository.

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `Failed to clone ...` | Check internet connection and that you have access to the repos |
| `OPENAI_API_KEY is empty` | Edit `../ml-datascience/api/.env` |
| `... still has a placeholder value` | Replace the example value with your real credentials |
| `Docker daemon is not running` | Open Docker Desktop and wait for it to fully start |
| `git: command not found` | Install git from [git-scm.com](https://git-scm.com) |
| Google login fails | Make sure `http://localhost:3000/api/auth/callback/google` is added in Google Cloud Console |
| Port 3000 or 8000 in use | Mac/Linux: `lsof -i :3000` then kill PID · Windows: `netstat -ano \| findstr :3000` then `taskkill /PID <pid> /F` |
| Code changes not reflected | Hot reload handles this automatically — no need to rebuild |
| After `git pull` on web-app or ml-datascience | Run `python run.py --docker-build` to rebuild images |
