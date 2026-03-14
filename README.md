# installation-core — PrepPilot Setup & Launcher

This folder contains scripts to install dependencies and launch both PrepPilot services — the ML backend and the web app — with a single command.

---

## Scripts Overview

| Script | Platform | Purpose |
|---|---|---|
| `install.sh` | Mac / Linux | Install all dependencies (run once) |
| `install.bat` | Windows | Install all dependencies (run once) |
| `start.sh` | Mac / Linux | Launch both services |
| `start.bat` | Windows | Launch both services (in separate windows) |

---

## Quick Start

### Mac / Linux

```bash
# Step 1 — install dependencies (first time only)
bash installation-core/install.sh

# Step 2 — fill in environment files (see setup below)

# Step 3 — launch both services
bash installation-core/start.sh
```

### Windows

```bat
REM Step 1 — install dependencies (first time only)
installation-core\install.bat

REM Step 2 — fill in environment files (see setup below)

REM Step 3 — launch both services
installation-core\start.bat
```

---

## Prerequisites

| Tool | Minimum Version | Install |
|---|---|---|
| Python | 3.10+ | [python.org](https://python.org) · Mac: `brew install python` · Windows: check **"Add to PATH"** during install |
| Node.js | 18+ | [nodejs.org](https://nodejs.org) · Mac: `brew install node` |
| npm | 9+ | Bundled with Node.js |
| OpenAI API key | — | [platform.openai.com](https://platform.openai.com) |
| MongoDB Atlas URI | — | [mongodb.com/atlas](https://www.mongodb.com/atlas) |
| Google OAuth credentials | — | [console.cloud.google.com](https://console.cloud.google.com) (setup below) |

---

## First-Time Setup

### Step 1 — Run the installer

**Mac / Linux:**
```bash
bash installation-core/install.sh
```

**Windows:**
```bat
installation-core\install.bat
```

The installer will:
- Create a Python virtual environment in `ml-datascience/.venv`
- Install all Python dependencies from `requirements.txt`
- Install Node dependencies in `web-app/node_modules`
- Create blank `.env` and `.env.local` template files if they don't exist

---

### Step 2 — Configure the ML backend

Edit `ml-datascience/api/.env`:

```env
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini    # optional — this is the default
```

Get your OpenAI API key at [platform.openai.com/api-keys](https://platform.openai.com/api-keys).

---

### Step 3 — Set up Google OAuth

You need a Google OAuth 2.0 client to enable login.

1. Go to [console.cloud.google.com](https://console.cloud.google.com)
2. Create a new project (or select an existing one)
3. Navigate to **APIs & Services → Credentials**
4. Click **Create Credentials → OAuth 2.0 Client ID**
5. Set Application type to **Web application**
6. Under **Authorized redirect URIs**, click **Add URI** and enter:
   ```
   http://localhost:3000/api/auth/callback/google
   ```
7. Click **Save**
8. Copy the **Client ID** and **Client Secret**

> **Important:** The redirect URI `http://localhost:3000/api/auth/callback/google` must be added exactly as shown. Without it, Google will reject the OAuth callback and login will fail.

---

### Step 4 — Set up MongoDB Atlas

1. Go to [mongodb.com/atlas](https://www.mongodb.com/atlas) and create a free cluster
2. Create a database user with read/write access
3. Add your IP address to the **Network Access** allowlist (or use `0.0.0.0/0` for development)
4. Click **Connect → Drivers** and copy the connection string

---

### Step 5 — Configure the web app

Edit `web-app/.env.local`:

```env
MONGODB_URI=mongodb+srv://<user>:<password>@<cluster>.mongodb.net/preppilot?retryWrites=true&w=majority
GOOGLE_CLIENT_ID=<your-google-client-id>
GOOGLE_CLIENT_SECRET=<your-google-client-secret>
AUTH_SECRET=<random-64-char-string>
NEXTAUTH_URL=http://localhost:3000
ML_BACKEND_URL=http://localhost:8000
```

Generate a secure `AUTH_SECRET`:

**Mac / Linux:**
```bash
npx auth secret
```

**Windows:**
```bat
npx auth secret
```

Or generate manually:
```bash
openssl rand -base64 48
```

---

### Step 6 — Launch

**Mac / Linux:**
```bash
bash installation-core/start.sh
```

**Windows:**
```bat
installation-core\start.bat
```

Expected output after startup:
```
============================================
  ML backend → http://localhost:8000
  Web app    → http://localhost:3000
============================================
  Press Ctrl-C to stop both services.
```

On Windows, both services open in separate terminal windows.

---

## Services at a Glance

| Service | URL | Description |
|---|---|---|
| Web App | http://localhost:3000 | Next.js chat interface |
| ML Backend | http://localhost:8000 | FastAPI data-science agent |
| Health Check | http://localhost:8000/health | Returns `{"status":"ok"}` |
| API Docs | http://localhost:8000/docs | Swagger UI |

---

## What the Scripts Do

```
install.sh / install.bat
├── Check Python and Node.js are installed
├── Create ml-datascience/.venv (if not present)
├── pip install -r requirements.txt + pip install -e .
├── npm install in web-app/
├── Create ml-datascience/api/.env from .env.example (if missing)
└── Create web-app/.env.local template (if missing)

start.sh (Mac/Linux)
├── Activate .venv and validate OPENAI_API_KEY
├── Start: uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload  (background)
├── Start: npm run dev  (background)
├── Wait for both processes
└── Ctrl-C gracefully kills both services

start.bat (Windows)
├── Validate .env files and OPENAI_API_KEY
├── Open "PrepPilot - ML Backend" in a new terminal window
├── Open "PrepPilot - Web App" in a new terminal window
└── Close either window or press Ctrl-C inside to stop that service
```

---

## Subsequent Runs

Already-installed dependencies are skipped — re-running `install.sh`/`install.bat` is safe and fast. Startup only takes a few seconds on subsequent `start.sh`/`start.bat` runs.

---

## Stopping Services

**Mac / Linux:** Press `Ctrl-C` in the terminal running `start.sh`. Both services are gracefully shut down.

**Windows:** Close the "PrepPilot - ML Backend" and "PrepPilot - Web App" terminal windows, or press `Ctrl-C` in each.

---

## Troubleshooting

| Problem | Cause | Fix |
|---|---|---|
| `OPENAI_API_KEY is not set` | Missing or empty `.env` | Edit `ml-datascience/api/.env` and add your key |
| `Please fill in .env.local` | Web app env file is blank | Fill in all values in `web-app/.env.local` and re-run |
| Google login fails / redirect error | Redirect URI not registered | Add `http://localhost:3000/api/auth/callback/google` in Google Cloud Console |
| Port 8000 already in use | Another process on that port | Mac/Linux: `lsof -i :8000` then kill the PID · Windows: `netstat -ano \| findstr :8000` then `taskkill /PID <pid> /F` |
| Port 3000 already in use | Another Next.js dev server | Mac/Linux: `lsof -i :3000` then kill the PID · Windows: `netstat -ano \| findstr :3000` then `taskkill /PID <pid> /F` |
| `python3: command not found` | Python not installed or not in PATH | Mac: `brew install python` · Windows: reinstall Python with "Add to PATH" checked |
| `npm: command not found` | Node.js not installed | Install from [nodejs.org](https://nodejs.org) |
| Node deps out of date | Pulled new changes from git | Delete `web-app/node_modules` and re-run `install.sh`/`install.bat` |
| Python deps out of date | Pulled new changes from git | Delete `ml-datascience/.venv` and re-run `install.sh`/`install.bat` |
| `.venv\Scripts\activate` error on Windows | Python venv not created | Run `install.bat` first |

---

## Manual Launch (without these scripts)

**ML backend:**

Mac/Linux:
```bash
cd ml-datascience
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt && pip install -e .
uvicorn api.main:app --reload --port 8000
```

Windows:
```bat
cd ml-datascience
python -m venv .venv
.venv\Scripts\activate.bat
pip install -r requirements.txt
pip install -e .
uvicorn api.main:app --reload --port 8000
```

**Web app (separate terminal):**

Mac/Linux:
```bash
cd web-app
npm install
npm run dev
```

Windows:
```bat
cd web-app
npm install
npm run dev
```

---

## File Structure

```
installation-core/
├── install.sh     # Dependency installer (Mac / Linux)
├── install.bat    # Dependency installer (Windows)
├── start.sh       # Unified launcher (Mac / Linux)
├── start.bat      # Unified launcher (Windows)
└── README.md      # This file
```
