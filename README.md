# installation-core — One-Command Launcher

This folder contains the unified startup script that launches **both** PrepPilot services — the ML backend and the web app — with a single command.

---

## Quick Start

```bash
bash installation-core/start.sh
```

Run from the project root (`seniorproject/`) or any path using the full path to `start.sh`.

---

## What `start.sh` Does

```
1. ML-Datascience  (FastAPI — port 8000)
   ├── Creates Python virtual environment (.venv) if not present
   ├── Installs / upgrades Python dependencies from requirements.txt
   ├── Installs the local ai_data_science_team package (pip install -e .)
   ├── Loads environment variables from ml-datascience/api/.env
   ├── Checks OPENAI_API_KEY is set (exits with error if missing)
   └── Starts: uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload

2. Web-App  (Next.js — port 3000)
   ├── Installs Node dependencies (npm install) if node_modules is absent
   ├── Creates a blank .env.local template if none exists (then exits with a warning)
   └── Starts: npm run dev

3. Waits for both processes
   └── Ctrl-C gracefully kills both services
```

---

## Prerequisites

| Tool | Minimum Version | Install |
|---|---|---|
| Python | 3.10+ | [python.org](https://python.org) or `brew install python` |
| Node.js | 18+ | [nodejs.org](https://nodejs.org) or `brew install node` |
| npm | 9+ | Bundled with Node.js |
| OpenAI API key | — | [platform.openai.com](https://platform.openai.com) |
| MongoDB Atlas URI | — | [mongodb.com/atlas](https://www.mongodb.com/atlas) |
| Google OAuth credentials | — | [console.cloud.google.com](https://console.cloud.google.com) |

---

## First-Time Setup

### Step 1 — ML Backend environment

```bash
cp ../ml-datascience/api/.env.example ../ml-datascience/api/.env
```

Edit `ml-datascience/api/.env`:
```env
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini   # optional, this is the default
```

### Step 2 — Web App environment

If `web-app/.env.local` does not exist, `start.sh` creates a blank template and exits with a warning. Fill it in before re-running:

```env
MONGODB_URI=mongodb+srv://<user>:<password>@<cluster>.mongodb.net/preppilot?retryWrites=true&w=majority
GOOGLE_CLIENT_ID=<your-google-client-id>
GOOGLE_CLIENT_SECRET=<your-google-client-secret>
AUTH_SECRET=<64-char-random-string>
NEXTAUTH_URL=http://localhost:3000
ML_BACKEND_URL=http://localhost:8000
```

Generate `AUTH_SECRET` with:
```bash
npx auth secret
```

> See `web-app/README.md` for detailed instructions on obtaining each value.

### Step 3 — Launch

```bash
bash installation-core/start.sh
```

Expected output after startup:
```
============================================
  ML backend → http://localhost:8000
  Web app    → http://localhost:3000
============================================
  Press Ctrl-C to stop both services.
```

---

## Services at a Glance

| Service | URL | Description |
|---|---|---|
| Web App | http://localhost:3000 | Next.js chat interface |
| ML Backend | http://localhost:8000 | FastAPI data-science agent |
| Health Check | http://localhost:8000/health | Returns `{"status":"ok"}` |
| Swagger Docs | http://localhost:8000/docs | Auto-generated API docs |

---

## Subsequent Runs

Already-installed dependencies are skipped — startup only takes a few seconds on subsequent runs.

---

## Stopping

Press **Ctrl-C**. The script traps `INT`/`TERM` signals and gracefully shuts down both processes before exiting.

---

## Troubleshooting

| Problem | Cause | Fix |
|---|---|---|
| `OPENAI_API_KEY is not set` | Missing or empty `.env` | Copy `.env.example` → `.env` and add your key |
| `Please fill in .env.local` | Web app env file was just created blank | Fill in all values and re-run |
| Port 8000 already in use | Another process on that port | `lsof -i :8000` → kill the PID |
| Port 3000 already in use | Another Next.js dev server running | `lsof -i :3000` → kill the PID |
| `python3: command not found` | Python not installed or not in PATH | `brew install python` or use `pyenv` |
| `npm: command not found` | Node.js not installed | `brew install node` or use `nvm` |
| Node deps out of date | Changes pulled from git | Delete `web-app/node_modules` and re-run |
| Python deps out of date | Changes pulled from git | Delete `ml-datascience/.venv` and re-run |

---

## File Structure

```
installation-core/
├── start.sh     # Unified launcher for both services
└── README.md    # This file
```

---

## Manual Launch (without this script)

**ML backend:**
```bash
cd ml-datascience
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt && pip install -e .
source api/.env
uvicorn api.main:app --reload --port 8000
```

**Web app (separate terminal):**
```bash
cd web-app
npm install
npm run dev
```
