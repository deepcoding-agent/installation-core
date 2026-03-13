# PrepPilot — Core Launcher

One command to install and start the entire PrepPilot stack.

---

## Project Structure

```
seniorproject/
├── core/               ← you are here
│   ├── start.sh        — unified launcher script
│   └── README.md
├── ml-datascience/     — Python FastAPI agent backend (port 8000)
└── web-app/            — Next.js frontend (port 3000)
```

---

## Prerequisites

| Tool | Version | Install |
|---|---|---|
| Python | 3.10+ | [python.org](https://python.org) |
| Node.js | 18+ | [nodejs.org](https://nodejs.org) |
| npm | 9+ | bundled with Node.js |

---

## First-time Setup

### 1. ML Backend — API key

Copy the example env file and add your OpenAI key:

```bash
cp ml-datascience/api/.env.example ml-datascience/api/.env
```

Open `ml-datascience/api/.env` and set:

```env
OPENAI_API_KEY=sk-...
```

### 2. Web App — environment variables

Copy the example or let the launcher create a template for you (it will exit and ask you to fill it in on first run).

```bash
cp web-app/.env.local.example web-app/.env.local   # if the example exists
```

Then fill in `web-app/.env.local`:

```env
MONGODB_URI=mongodb+srv://<user>:<password>@<cluster>.mongodb.net/preppilot?retryWrites=true&w=majority
GOOGLE_CLIENT_ID=<your-google-client-id>
GOOGLE_CLIENT_SECRET=<your-google-client-secret>
AUTH_SECRET=<random-64-char-hex>
NEXTAUTH_URL=http://localhost:3000
ML_BACKEND_URL=http://localhost:8000
```

> See `web-app/ARCHITECTURE.md` for detailed instructions on obtaining each value.

---

## Running the App

```bash
bash core/start.sh
```

Run this from the **project root** (`seniorproject/`), or from anywhere using the full path:

```bash
bash ~/seniorproject/core/start.sh
```

### What happens on first run

| Step | Action |
|---|---|
| Python venv | Creates `.venv` inside `ml-datascience/` |
| Python deps | Runs `pip install -r requirements.txt` + installs the local package |
| Node deps | Runs `npm install` inside `web-app/` |
| Env check | Exits early with a helpful message if required env vars are missing |
| Start | Launches both services concurrently |

### What happens on subsequent runs

Already-installed dependencies are skipped — startup takes only a few seconds.

---

## Services

| Service | URL | Description |
|---|---|---|
| Web App | http://localhost:3000 | Next.js chat interface |
| ML Backend | http://localhost:8000 | FastAPI data-science agent |
| API Health | http://localhost:8000/health | Returns `{"status":"ok"}` |
| API Docs | http://localhost:8000/docs | Auto-generated Swagger UI |

---

## Stopping

Press **Ctrl-C** in the terminal. The script will cleanly shut down both services.

---

## Troubleshooting

**`OPENAI_API_KEY is not set`**
→ Make sure `ml-datascience/api/.env` exists and contains a valid key.

**`MONGODB_URI` / auth errors**
→ Ensure the URI ends with `/preppilot?...` (the database name must be present before the `?`).

**Port already in use**
→ Kill the conflicting process or change the port:
```bash
# Find what's using port 8000
lsof -i :8000
# Or change the port in start.sh (--port 8000) and .env.local (ML_BACKEND_URL)
```

**Node modules out of date after pulling changes**
→ Delete `web-app/node_modules` and re-run `start.sh` — it will reinstall automatically.

**Python deps out of date**
→ Delete `ml-datascience/.venv` and re-run `start.sh` — it will recreate and reinstall.
