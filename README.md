# installation-core — PrepPilot Setup & Launcher

One repo to clone. One command to run. Everything else is automatic.

---

## What is PrepPilot?

**PrepPilot** is a full-stack AI-powered data science preparation platform. Users upload CSV datasets, chat with AI agents that analyze, clean, visualize, and prepare data for machine learning — all through a web interface.

| | |
|---|---|
| **Stack** | Next.js 16 (frontend) + FastAPI (backend) + Anthropic Claude / OpenAI GPT + Plotly + Docker |
| **Handlers** | 106 pre-built handlers across 5 categories (stats, clean, transform, viz, feature) |
| **Charts** | 22 interactive Plotly chart types with minimal design theme |
| **AI Agents** | Planner, Step Executor, Code Generator, Result Interpreter, Context Analyzer |
| **Pipeline** | 10-step automated ML data preparation with AI-optimized config |
| **Auth** | Google OAuth via NextAuth v5 |
| **Database** | SQLite (dev) / MongoDB (prod) |

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

Open the app at **http://localhost:3000**

---

## Prerequisites

| Tool | Minimum | Install |
|------|---------|---------|
| Python | 3.10+ | [python.org](https://python.org) |
| Git | any | [git-scm.com](https://git-scm.com) |
| Docker Desktop | latest | [docker.com](https://docker.com) *(Docker mode)* |
| Node.js | 18+ | [nodejs.org](https://nodejs.org) *(Local mode)* |

---

## First-Time Setup

### Step 1 — Clone this repo

```bash
git clone https://github.com/deepcoding-agent/installation-core.git installation-core
```

> `web-app` and `ml-datascience` will be cloned automatically on first run.

### Step 2 — Configure the ML backend

The first run creates `../ml-datascience/api/.env` from the example. Open it and fill in:

```env
# At least one AI provider is required
ANTHROPIC_API_KEY=sk-ant-...         # Anthropic Claude
OPENAI_API_KEY=sk-...                # OpenAI GPT (default provider)

# Model defaults
ANTHROPIC_MODEL=claude-sonnet-4-6    # used when user selects Claude
OPENAI_MODEL=gpt-4o-mini             # default model for all AI operations

LOG_LEVEL=info
```

Get your keys:
- Anthropic: [console.anthropic.com](https://console.anthropic.com)
- OpenAI: [platform.openai.com](https://platform.openai.com)

### Step 3 — Configure the web app

The first run creates `../web-app/.env.local` from the example. Fill in:

```env
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret
AUTH_SECRET=<run: openssl rand -hex 32>
NEXTAUTH_URL=http://localhost:3000
ML_BACKEND_URL=http://localhost:8000
DATABASE_URL="file:./prisma/dev.db"
```

Generate `AUTH_SECRET`:
```bash
openssl rand -hex 32
```

### Step 4 — Run

```bash
python run.py --docker-build
```

---

## Commands

```bash
# Docker (recommended)
python run.py --docker-build     # first run or after git pull
python run.py --docker           # subsequent runs (no rebuild)
python run.py --docker-down      # stop all containers

# Local (no Docker)
python run.py                    # install deps + start both services
python run.py --install          # install deps only
python run.py --start            # start only (deps already installed)
```

---

## Services

| Service | URL |
|---------|-----|
| Web App | http://localhost:3000 |
| ML Backend API | http://localhost:8000 |
| API Docs (Swagger) | http://localhost:8000/docs |
| Health Check | http://localhost:8000/health |

---

## Key Features

### Chat Commands

| Command | Description |
|---------|-------------|
| `/cleaning` | AI analyzes dataset, decides what to clean, executes automatically |
| `/ml-prepare` | AI prepares train/test splits with optimized preprocessing |
| `/ml-prepare price` | ML preparation with specified target column |
| Natural language | Ask anything: "fill missing values", "show distribution of price", "remove outliers" |

### Handler Categories (106 total)

| Category | Count | Examples |
|----------|-------|----------|
| **Stats** | 18 | describe, correlation, normality test, class balance, outlier report |
| **Clean** | 20 | fill nulls, remove duplicates, fix types, clip outliers, map values |
| **Transform** | 26 | filter, sort, pivot, melt, encode, scale, rolling, rank |
| **Visualization** | 22 | bar, pie, scatter, histogram, heatmap, violin, QQ, density |
| **Feature Engineering** | 20 | PCA, importance, lag, text features, target encode, power transform |

### AI-Driven Features

| Feature | What it does |
|---------|-------------|
| **Auto-Clean** | AI reads dataset, identifies issues (nulls, dupes, type mismatches, outliers), plans and executes cleaning operations |
| **Auto-Prepare** | AI analyzes target column, decides optimal preprocessing config (scaling, encoding, outlier treatment), runs 10-step pipeline |
| **Smart Chart Selection** | AI picks the right chart type based on user intent — pie for proportions, histogram for distributions, scatter for relationships |
| **AI Planner** | Every user message is routed through an LLM planner that decides handler vs code generation |

### Output Formats

| Type | Description |
|------|-------------|
| **Inline Table** | Query results shown in chat, downloadable as CSV |
| **Interactive Charts** | Plotly charts with fullscreen, zoom, hover |
| **Generated Datasets** | New datasets saved to topbar, reusable in next steps |
| **ML-Ready Folder** | 4 files (X_train, X_test, y_train, y_test) + metadata, downloadable as ZIP |

---

## Architecture

```
User (browser)
  │
  ▼
┌──────────────────────────────────────────────────┐
│  Next.js 16 (web-app)           port 3000        │
│  ├── Landing page (Scale.ai-inspired design)     │
│  ├── Google OAuth (NextAuth v5)                  │
│  ├── Chat UI with dataset management             │
│  └── API routes (thin proxies to FastAPI)        │
└──────────────────────┬───────────────────────────┘
                       │ HTTP
                       ▼
┌──────────────────────────────────────────────────┐
│  FastAPI (ml-datascience)       port 8000        │
│  ├── POST /chat          → DS-Agent orchestrator │
│  ├── POST /auto-clean    → AI auto-cleaning      │
│  ├── POST /auto-prepare  → AI ML preparation     │
│  ├── POST /prepare       → 10-step pipeline      │
│  ├── POST /eda-report    → structured EDA        │
│  ├── POST /suggest-target → AI target suggestion │
│  └── GET  /models        → available AI models   │
│                                                  │
│  AI Agents:                                      │
│  ├── Planner → routes to handler or codegen      │
│  ├── Step Executor → runs handlers sequentially  │
│  ├── Code Generator → LLM writes Python          │
│  ├── Result Interpreter → explains results       │
│  └── Context Analyzer → dataset profiling        │
│                                                  │
│  106 Handlers:                                   │
│  ├── stats (18)  clean (20)  transform (26)      │
│  ├── viz (22)    feature (20)                    │
│  └── Sandboxed exec() for generated code         │
└──────────────────────────────────────────────────┘
```

---

## Project Structure

```
seniorproject/
├── installation-core/       ← this repo — clone first
│   ├── run.py               single-command launcher
│   ├── docker-compose.yml   orchestrates both services
│   └── README.md
├── web-app/                 ← cloned automatically
│   ├── src/app/             Next.js pages + API routes
│   ├── prisma/              database schema
│   └── public/              static assets
└── ml-datascience/          ← cloned automatically
    ├── api/
    │   ├── agents/          AI agents (planner, executor, etc.)
    │   ├── handlers/        106 pre-built data operations
    │   ├── routes/          FastAPI endpoints
    │   └── sandbox.py       sandboxed code execution
    └── docs/                handler reference
```

Each folder is its own git repository.

---

## Google OAuth Setup

1. Go to [console.cloud.google.com](https://console.cloud.google.com)
2. Create a project, then go to **APIs & Services > Credentials**
3. Click **Create Credentials > OAuth 2.0 Client ID**
4. Application type: **Web application**
5. Add authorized redirect URI:
   ```
   http://localhost:3000/api/auth/callback/google
   ```
6. Copy **Client ID** and **Client Secret** into `web-app/.env.local`

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `Failed to clone ...` | Check internet and repo access |
| `OPENAI_API_KEY is empty` | Edit `../ml-datascience/api/.env` |
| `... still has a placeholder value` | Replace example values with real credentials |
| `Docker daemon is not running` | Open Docker Desktop and wait for startup |
| Google login fails | Verify redirect URI in Google Cloud Console |
| Port 3000/8000 in use | `lsof -i :3000` then kill the PID |
| Code changes not reflected | Hot reload is automatic; rebuild only after `git pull` |
| After `git pull` | Run `python run.py --docker-build` to rebuild |
| Hydration error in browser | Stop dev server, `rm -rf .next`, restart |

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 16, TypeScript, Tailwind CSS, MUI Icons |
| Charts | Plotly.js (react-plotly.js, dynamic import) |
| Auth | NextAuth v5 + Google OAuth |
| Database | Prisma ORM + SQLite (dev) / MongoDB (prod) |
| Backend | FastAPI, Python 3.10+ |
| AI | Anthropic Claude, OpenAI GPT (multi-provider) |
| ML | scikit-learn, pandas, numpy |
| Infra | Docker Compose, hot reload |

---

*Senior Project — Computer Engineering, KMUTT 2025*
