# installation-core — DS-Agent Setup & Launcher

Central control for all services. One command to install, one command to run — works on Mac, Linux, and Windows.

---

## Repository Structure

This project uses **4 separate git repositories** that live side-by-side:

```
seniorproject/
├── installation-core/    ← this repo — controls everything
├── web-app/              ← Next.js frontend
├── ml-datascience/       ← FastAPI ML backend
└── docs/                 ← documentation
```

Clone all repos into the **same parent folder** before continuing.

---

## Prerequisites

| Tool | Minimum | Install |
|------|---------|---------|
| Python | 3.10+ | [python.org](https://python.org) · Mac: `brew install python` |
| Node.js | 18+ | [nodejs.org](https://nodejs.org) · Mac: `brew install node` |
| npm | 9+ | Bundled with Node.js |
| Docker Desktop | latest | [docker.com](https://docker.com) *(Docker mode only)* |
| OpenAI API key | — | [platform.openai.com/api-keys](https://platform.openai.com/api-keys) |
| Google OAuth credentials | — | [console.cloud.google.com](https://console.cloud.google.com) |

---

## Two Ways to Run

| Mode | When to use |
|------|-------------|
| **Docker** | Share with teammates, consistent environment, recommended |
| **Local** | Faster startup, direct access to logs, no Docker needed |

---

## Option A — Docker (Recommended)

### Step 1 — Clone all repositories

```bash
mkdir seniorproject && cd seniorproject
git clone <installation-core-repo-url> installation-core
git clone <web-app-repo-url>           web-app
git clone <ml-datascience-repo-url>    ml-datascience
```

### Step 2 — Configure environment files

**ML backend** — copy and fill in `ml-datascience/api/.env`:

```bash
cp ml-datascience/api/.env.example ml-datascience/api/.env
```

Edit `ml-datascience/api/.env`:
```env
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini
```

**Web app** — copy and fill in `web-app/.env.local`:

```bash
cp web-app/.env.local.example web-app/.env.local
```

Edit `web-app/.env.local`:
```env
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret
AUTH_SECRET=your-random-secret
NEXTAUTH_URL=http://localhost:3000
ML_BACKEND_URL=http://localhost:8000
DATABASE_URL="file:./prisma/dev.db"
```

> See [Google OAuth Setup](#google-oauth-setup) below for how to get `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET`.

### Step 3 — Build and start

```bash
python installation-core/run.py --docker-build
```

This will:
- Verify Docker is running
- Build Docker images for both services
- Start the ML backend on port **8000**
- Start the Web app on port **3000**
- Mount source code so code changes reflect in real-time (hot reload)

### Step 4 — Open the app

| Service | URL |
|---------|-----|
| Web App | http://localhost:3000 |
| ML Backend API | http://localhost:8000 |
| API Docs (Swagger) | http://localhost:8000/docs |

---

### Docker — Daily Commands

```bash
# Start (after first build — fast)
python installation-core/run.py --docker

# Stop
python installation-core/run.py --docker-down

# Rebuild images (after pulling new code or changing dependencies)
python installation-core/run.py --docker-build
```

---

## Option B — Local (No Docker)

### Step 1 — Clone all repositories

Same as Docker Step 1.

### Step 2 — Configure environment files

Same as Docker Step 2.

### Step 3 — Install and start

```bash
python installation-core/run.py
```

This single command:
1. Checks Python 3.10+, Node.js 18+, npm
2. Creates `ml-datascience/.venv` and installs Python dependencies
3. Runs `npm install` in `web-app/`
4. Checks all `.env` files are filled in
5. Starts both services with hot reload
6. Press **Ctrl-C** to gracefully stop both

### Step 4 — Open the app

Same URLs as Docker mode.

---

### Local — Daily Commands

```bash
# Install deps only (after pulling new code)
python installation-core/run.py --install

# Start only (deps already installed)
python installation-core/run.py --start

# Install + start (safe to run every time)
python installation-core/run.py
```

---

## All Commands Reference

```bash
python installation-core/run.py                 # local: install deps + start
python installation-core/run.py --install       # local: install deps only
python installation-core/run.py --start         # local: start only

python installation-core/run.py --docker        # Docker: start (no rebuild)
python installation-core/run.py --docker-build  # Docker: rebuild images + start
python installation-core/run.py --docker-down   # Docker: stop all containers
```

---

## Google OAuth Setup

1. Go to [console.cloud.google.com](https://console.cloud.google.com)
2. Create a new project (or select existing)
3. Go to **APIs & Services → Credentials**
4. Click **Create Credentials → OAuth 2.0 Client ID**
5. Set Application type to **Web application**
6. Under **Authorized redirect URIs**, add:
   ```
   http://localhost:3000/api/auth/callback/google
   ```
7. Click **Save** — copy the **Client ID** and **Client Secret** into `web-app/.env.local`

> The redirect URI must match exactly. Without it, Google login will fail.

---

## Generate AUTH_SECRET

```bash
# Mac / Linux
openssl rand -hex 32

# Any platform (requires Node.js)
npx auth secret
```

Paste the output as `AUTH_SECRET` in `web-app/.env.local`.

---

## File Structure

```
installation-core/
├── run.py              ← single launcher for all modes (Mac/Linux/Windows)
├── docker-compose.yml  ← Docker service definitions
├── install.sh          ← dependency installer (Mac / Linux)
├── install.bat         ← dependency installer (Windows)
├── start.sh            ← service starter (Mac / Linux)
├── start.bat           ← service starter (Windows)
└── README.md           ← this file
```

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `OPENAI_API_KEY is empty` | Edit `ml-datascience/api/.env` and add your key |
| `Missing values in web-app/.env.local` | Fill in `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `AUTH_SECRET` |
| Google login fails | Add `http://localhost:3000/api/auth/callback/google` in Google Cloud Console |
| `Docker daemon is not running` | Open Docker Desktop and wait for it to fully start |
| Port 3000 or 8000 already in use | Kill the process using that port: `lsof -i :3000` (Mac/Linux) or `netstat -ano \| findstr :3000` (Windows) |
| `python3: command not found` | Install Python from [python.org](https://python.org) and make sure it's in PATH |
| `npm: command not found` | Install Node.js from [nodejs.org](https://nodejs.org) |
| Code changes not reflected (Docker) | Make sure you're not running `--docker-build` unnecessarily — hot reload handles code changes automatically |
| Dependencies out of date after `git pull` | Local: run `--install`. Docker: run `--docker-build` |
