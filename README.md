# PrepPilot — Installation & Setup Guide

One repo to clone. One command to run. Works on **macOS, Linux, and Windows**.

---

## What is PrepPilot?

**PrepPilot** is an AI-powered data science platform. Upload datasets, chat with AI agents that analyze, clean, visualize, and prepare data for machine learning — all through a web interface.

| | |
| --- | --- |
| **Stack** | Next.js 16 + FastAPI + Anthropic Claude / OpenAI GPT + Plotly + Docker |
| **Handlers** | 417 pre-built handlers across 7 categories |
| **Charts** | 56 interactive Plotly chart types |
| **File Formats** | 20+ upload formats (CSV, Excel, JSON, YAML, Parquet, etc.) |
| **AI Agents** | Router, Planner, Step Executor, Code Generator, Interpreter |
| **Commands** | `/cleaning`, `/ml-prepare`, `/insights`, `/report`, `/train` |
| **Auth** | Google OAuth via NextAuth v5 |
| **Database** | SQLite (dev) / MongoDB (prod) |

---

## Quick Start (Docker — Recommended)

```bash
git clone https://github.com/deepcoding-agent/installation-core.git
cd installation-core
python run.py --docker-build
```

That's it. Open **http://localhost:3000** when both services are up.

> `run.py` auto-clones `web-app` and `ml-datascience` if missing, checks `.env` files, builds Docker images, and starts everything.

---

## Prerequisites

### For Docker mode (recommended)

| Tool | Minimum | Install |
| --- | --- | --- |
| Python | 3.10+ | [python.org](https://python.org) |
| Git | any | [git-scm.com](https://git-scm.com) |
| Docker Desktop | latest | [docker.com](https://docker.com) |

> **Windows users**: Docker Desktop must use the **WSL 2 backend** (default on new installs). Check: Docker Desktop > Settings > General > "Use the WSL 2 based engine" must be checked.

### For manual mode (no Docker)

| Tool | Minimum | Install |
| --- | --- | --- |
| Python | 3.10+ | [python.org](https://python.org) |
| Git | any | [git-scm.com](https://git-scm.com) |
| Node.js | 18+ | [nodejs.org](https://nodejs.org) |
| npm | 9+ | comes with Node.js |

---

## Environment Configuration

Both repos need `.env` files before first run. `run.py` creates them automatically from examples, but you must fill in real values.

### ML Backend — `ml-datascience/api/.env`

```env
# At least one AI provider is required
OPENAI_API_KEY=sk-...                # OpenAI GPT (default provider)
ANTHROPIC_API_KEY=sk-ant-...         # Anthropic Claude (optional)

# Default models
OPENAI_MODEL=gpt-4o-mini
ANTHROPIC_MODEL=claude-sonnet-4-6

LOG_LEVEL=info
```

Get your keys:
- OpenAI: [platform.openai.com/api-keys](https://platform.openai.com/api-keys)
- Anthropic: [console.anthropic.com](https://console.anthropic.com)

### Web App — `web-app/.env.local`

```env
GOOGLE_CLIENT_ID=your-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-secret
AUTH_SECRET=<generate with: openssl rand -hex 32>
NEXTAUTH_URL=http://localhost:3000
ML_BACKEND_URL=http://localhost:8000
DATABASE_URL="file:./prisma/dev.db"
```

Generate `AUTH_SECRET`:

```bash
# macOS / Linux
openssl rand -hex 32

# Windows (PowerShell)
-join ((1..32) | ForEach-Object { '{0:x2}' -f (Get-Random -Max 256) })

# Or use Python (any OS)
python -c "import secrets; print(secrets.token_hex(32))"
```

### Google OAuth Setup

1. Go to [console.cloud.google.com](https://console.cloud.google.com)
2. Create a project > **APIs & Services** > **Credentials**
3. Click **Create Credentials** > **OAuth 2.0 Client ID**
4. Application type: **Web application**
5. Add authorized redirect URI: `http://localhost:3000/api/auth/callback/google`
6. Copy **Client ID** and **Client Secret** into `web-app/.env.local`

---

## Option A: Docker Mode (Recommended)

Best for: quick setup, consistent environments, no dependency conflicts.

### Commands

```bash
# First run (or after git pull to pick up new dependencies)
python run.py --docker-build

# Subsequent runs (fast — no rebuild)
python run.py --docker

# Stop all containers
python run.py --docker-down
```

Or run Docker Compose directly:

```bash
cd installation-core
docker compose up --build        # first run
docker compose up                # subsequent runs
docker compose down              # stop
```

### Hot Reload (Docker)

Both services support hot reload inside Docker. Edit files on your host machine and changes appear automatically:

| What you edit | Where on host | Effect |
| --- | --- | --- |
| Python backend code | `ml-datascience/api/**/*.py` | Uvicorn restarts automatically (~1-2s) |
| React components/pages | `web-app/src/**/*.tsx` | Next.js hot reloads (~0.5-1s) |
| Tailwind/PostCSS config | `web-app/tailwind.config.ts` | Next.js rebuilds styles |
| Prisma schema | `web-app/prisma/schema.prisma` | Run `docker compose exec web-app npx prisma db push` |
| Python dependencies | `ml-datascience/requirements.txt` | Rebuild: `python run.py --docker-build` |
| Node dependencies | `web-app/package.json` | Rebuild: `python run.py --docker-build` |

> **Windows/WSL2 note**: File polling is enabled automatically via `WATCHPACK_POLLING` and `WATCHFILES_FORCE_POLLING`. Hot reload works on all platforms, but may be slightly slower on Windows (~2-3s vs ~0.5s on macOS/Linux).

### Services

| Service | URL |
| --- | --- |
| Web App | [http://localhost:3000](http://localhost:3000) |
| ML Backend API | [http://localhost:8000](http://localhost:8000) |
| API Docs (Swagger) | [http://localhost:8000/docs](http://localhost:8000/docs) |
| Health Check | [http://localhost:8000/health](http://localhost:8000/health) |

---

## Option B: Manual Mode (No Docker)

Best for: full control, debugging, direct access to logs, or systems without Docker.

### macOS

```bash
# 1. Install prerequisites (if not already installed)
brew install python@3.11 node git

# 2. Clone repositories
git clone https://github.com/deepcoding-agent/installation-core.git
cd installation-core
# Auto-clone sibling repos:
python run.py --install
# OR clone manually:
cd ..
git clone https://github.com/deepcoding-agent/web-app.git
git clone https://github.com/deepcoding-agent/ml-datascience.git

# 3. Set up ML backend
cd ml-datascience
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# 4. Configure ML backend env
cp api/.env.example api/.env    # if example exists
nano api/.env                   # fill in API keys (see Environment section above)

# 5. Set up web app
cd ../web-app
npm install
npx prisma db push

# 6. Configure web app env
cp .env.local.example .env.local   # if example exists
nano .env.local                    # fill in values (see Environment section above)

# 7. Start both services (two terminal windows)

# Terminal 1 — ML Backend
cd ml-datascience
source .venv/bin/activate
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload

# Terminal 2 — Web App
cd web-app
npm run dev
```

### Linux (Ubuntu/Debian)

```bash
# 1. Install prerequisites
sudo apt update
sudo apt install -y python3.11 python3.11-venv python3-pip git
# Install Node.js 20
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs
# Install Thai fonts (required for matplotlib charts)
sudo apt install -y fonts-thai-tlwg fonts-noto-cjk

# 2. Clone repositories
git clone https://github.com/deepcoding-agent/installation-core.git
cd installation-core
python3 run.py --install
# OR clone manually (same as macOS steps 2 onward)

# 3. Set up ML backend
cd ../ml-datascience
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# 4. Configure ML backend env
cp api/.env.example api/.env
nano api/.env                   # fill in API keys

# 5. Set up web app
cd ../web-app
npm install
npx prisma db push

# 6. Configure web app env
cp .env.local.example .env.local
nano .env.local                 # fill in values

# 7. Start both services (two terminal windows)

# Terminal 1 — ML Backend
cd ml-datascience
source .venv/bin/activate
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload

# Terminal 2 — Web App
cd web-app
npm run dev
```

### Windows

```powershell
# 1. Install prerequisites
#    Download and install from:
#    - Python 3.11+: https://python.org (check "Add to PATH" during install)
#    - Node.js 20+:  https://nodejs.org
#    - Git:          https://git-scm.com

# 2. Clone repositories (PowerShell or Command Prompt)
git clone https://github.com/deepcoding-agent/installation-core.git
cd installation-core
python run.py --install
# OR clone manually:
cd ..
git clone https://github.com/deepcoding-agent/web-app.git
git clone https://github.com/deepcoding-agent/ml-datascience.git

# 3. Set up ML backend
cd ml-datascience
python -m venv .venv
.venv\Scripts\activate              # CMD
# or: .venv\Scripts\Activate.ps1   # PowerShell

pip install --upgrade pip
pip install -r requirements.txt

# 4. Configure ML backend env
copy api\.env.example api\.env      # if example exists
notepad api\.env                    # fill in API keys

# 5. Set up web app
cd ..\web-app
npm install
npx prisma db push

# 6. Configure web app env
copy .env.local.example .env.local  # if example exists
notepad .env.local                  # fill in values

# 7. Start both services (two terminal windows)

# Terminal 1 — ML Backend (CMD)
cd ml-datascience
.venv\Scripts\activate
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload

# Terminal 1 — ML Backend (PowerShell)
cd ml-datascience
.venv\Scripts\Activate.ps1
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload

# Terminal 2 — Web App
cd web-app
npm run dev
```

### One-Command Local Start (All Platforms)

If you prefer a single command that manages both services:

```bash
# Install everything + start both services
python run.py

# Or if deps are already installed:
python run.py --start
```

`run.py` starts both backend and frontend in the same terminal and handles Ctrl-C gracefully on all platforms.

---

## Commands Reference

| Command | Description |
| --- | --- |
| `python run.py` | Install deps + check env + start both services (local) |
| `python run.py --install` | Install dependencies only (no start) |
| `python run.py --start` | Start services only (skip install) |
| `python run.py --docker-build` | Build Docker images + start (first run / after pull) |
| `python run.py --docker` | Start Docker containers (no rebuild) |
| `python run.py --docker-down` | Stop all Docker containers |

---

## Project Structure

```
seniorproject/
├── installation-core/        <-- this repo (clone first)
│   ├── run.py                single-command launcher (all platforms)
│   ├── docker-compose.yml    Docker orchestration with hot reload
│   └── README.md             this file
│
├── web-app/                  <-- cloned automatically
│   ├── src/app/              Next.js pages + API routes
│   │   └── chatpage/         Main chat interface
│   ├── prisma/               Database schema (SQLite dev / MongoDB prod)
│   └── public/               Static assets
│
└── ml-datascience/           <-- cloned automatically
    └── api/
        ├── agents/           AI agents (router, planner, executor, etc.)
        ├── handlers/         417 pre-built data operations
        │   ├── stats/        56 statistics handlers
        │   ├── clean/        60 cleaning handlers
        │   ├── transform/    64 transform handlers
        │   ├── viz/          56 visualization handlers
        │   ├── feature/      63 feature engineering handlers
        │   ├── nlp/          56 NLP/text handlers
        │   └── analysis/     62 analysis handlers
        ├── routes/           FastAPI endpoints
        └── sandbox.py        Sandboxed code execution
```

Each folder is its own git repository.

---

## Chat Commands

| Command | Description |
| --- | --- |
| `/cleaning` | AI auto-cleans dataset (nulls, duplicates, types, outliers) |
| `/ml-prepare` | AI prepares train/test split with optimized preprocessing |
| `/ml-prepare price` | ML preparation with specified target column |
| `/train` | Auto ML — train 5-8 models, tune hyperparameters, evaluate with charts |
| `/train price` | Train with specified target column |
| `/insights` | Technical analysis — weaknesses, possible analyses, action plan |
| `/report` | Business intelligence report — market analysis, strategies, action items |
| Natural language | Ask anything: "show distribution of price", "remove outliers", "translate to English" |

---

## Architecture

```
User (browser)
  │
  ▼
┌──────────────────────────────────────────────────────────┐
│  Next.js 16 (web-app)                    port 3000       │
│  ├── Chat UI with dataset management                     │
│  ├── Google OAuth (NextAuth v5)                          │
│  └── API routes (thin proxies → FastAPI)                 │
└────────────────────┬─────────────────────────────────────┘
                     │ HTTP
                     ▼
┌──────────────────────────────────────────────────────────┐
│  FastAPI (ml-datascience)                port 8000       │
│  ├── POST /chat          → DS-Agent orchestrator         │
│  ├── POST /train         → Auto ML training pipeline     │
│  ├── POST /auto-clean    → AI auto-cleaning              │
│  ├── POST /auto-prepare  → AI ML preparation             │
│  ├── POST /prepare       → 10-step pipeline              │
│  ├── POST /insights      → AI insights report            │
│  ├── POST /documents     → Business intelligence report  │
│  ├── POST /eda-report    → Structured EDA                │
│  └── GET  /models        → Available AI models           │
│                                                          │
│  417 Handlers (7 categories):                            │
│  stats(56) clean(60) transform(64) viz(56)               │
│  feature(63) nlp(56) analysis(62)                        │
└──────────────────────────────────────────────────────────┘
```

---

## Troubleshooting

### All Platforms

| Problem | Fix |
| --- | --- |
| `OPENAI_API_KEY is empty` | Edit `ml-datascience/api/.env` and add your key |
| `... placeholder value` | Replace example values with real credentials |
| Port 3000 or 8000 in use | Kill the process using that port (see below) |
| Code changes not reflected | Hot reload is automatic; rebuild only after adding new dependencies |
| After `git pull` with new deps | Docker: `python run.py --docker-build`. Local: re-install deps |

### Docker-Specific

| Problem | Fix |
| --- | --- |
| `Docker daemon is not running` | Open Docker Desktop and wait for startup |
| Build fails on first run | Check internet connection (needs to download images + packages) |
| Volume mount permission error | Docker Desktop > Settings > Resources > File sharing: add project path |
| Hot reload not working | Files are polled automatically; wait 2-3s. If still stuck, restart containers |
| `depends_on: condition not met` | Backend health check failed — check `docker logs preppilot-backend` |
| Container keeps restarting | Check logs: `docker logs preppilot-backend` or `docker logs preppilot-frontend` |

### Windows-Specific

| Problem | Fix |
| --- | --- |
| Docker fails to start | Enable WSL 2: `wsl --install` in PowerShell (admin), restart, then reopen Docker Desktop |
| `python` not found | Install from python.org, check "Add Python to PATH" during install. Or use `py` instead of `python` |
| `npm` not found | Install Node.js from nodejs.org, restart terminal |
| PowerShell script execution blocked | Run: `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser` |
| Slow hot reload in Docker | Normal on Windows (~2-3s). File polling is enabled automatically |
| Line ending errors in Docker | Run: `git config --global core.autocrlf true` then re-clone |
| `\r: command not found` in Docker | Line ending issue — see above |

### macOS-Specific

| Problem | Fix |
| --- | --- |
| `command not found: python` | Use `python3` instead, or `brew install python@3.11` |
| Port in use | `lsof -i :3000` then `kill <PID>` |

### Linux-Specific

| Problem | Fix |
| --- | --- |
| Permission denied (Docker) | Add user to docker group: `sudo usermod -aG docker $USER` then log out/in |
| `externally-managed-environment` | Use `python3 -m venv .venv` (already handled by run.py) |
| Missing Thai fonts in charts | `sudo apt install fonts-thai-tlwg fonts-noto-cjk` |

---

## Kill Processes Using a Port

```bash
# macOS / Linux
lsof -i :3000        # find PID
kill <PID>

# Windows (CMD as admin)
netstat -ano | findstr :3000
taskkill /PID <PID> /F

# Windows (PowerShell)
Get-Process -Id (Get-NetTCPConnection -LocalPort 3000).OwningProcess | Stop-Process -Force
```

---

## Tech Stack

| Layer | Technology |
| --- | --- |
| Frontend | Next.js 16, TypeScript, Tailwind CSS, MUI Icons |
| Charts | Plotly.js (react-plotly.js, dynamic import, SSR-safe) |
| Auth | NextAuth v5 + Google OAuth |
| Database | Prisma ORM + SQLite (dev) / MongoDB (prod) |
| Backend | FastAPI, Python 3.11+ |
| AI | Anthropic Claude + OpenAI GPT (multi-provider, switchable) |
| ML | scikit-learn, pandas, numpy, statsmodels, XGBoost |
| Infra | Docker Compose, hot reload, cross-platform launcher |

---

*Senior Project — Applied computer science , KMUTT 2026*
