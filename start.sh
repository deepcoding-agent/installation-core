#!/usr/bin/env bash
# ============================================================
#  PrepPilot — one-command launcher
#  Run from anywhere:
#    bash /path/to/seniorproject/launch/start.sh
# ============================================================

set -e

# Resolve absolute path to the project root (parent of this script's folder)
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

ML_DIR="$ROOT/ml-datascience"
WEB_DIR="$ROOT/web-app"

# ── Colours ──────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
CYAN='\033[0;36m'; BOLD='\033[1m'; RESET='\033[0m'

log()  { echo -e "${CYAN}[launch]${RESET} $*"; }
ok()   { echo -e "${GREEN}[launch]${RESET} $*"; }
warn() { echo -e "${YELLOW}[launch]${RESET} $*"; }
die()  { echo -e "${RED}[launch] ERROR:${RESET} $*"; exit 1; }

# ── Cleanup on Ctrl-C / exit ─────────────────────────────────
cleanup() {
  echo ""
  log "Shutting down…"
  kill "$ML_PID" "$WEB_PID" 2>/dev/null || true
  wait "$ML_PID" "$WEB_PID" 2>/dev/null || true
  ok "All services stopped."
}
trap cleanup INT TERM EXIT

# ============================================================
#  1. ML-DATASCIENCE (FastAPI on :8000)
# ============================================================
log "${BOLD}Setting up ml-datascience…${RESET}"

cd "$ML_DIR"

# Python venv
if [ ! -d ".venv" ]; then
  log "Creating Python virtual environment…"
  python3 -m venv .venv
fi

source .venv/bin/activate

log "Installing Python dependencies (skipped if up-to-date)…"
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt
pip install --quiet -e .

# Load .env
if [ -f "api/.env" ]; then
  set -a; source api/.env; set +a
fi

if [ -z "$OPENAI_API_KEY" ]; then
  die "OPENAI_API_KEY is not set.\n  Copy  ml-datascience/api/.env.example  →  ml-datascience/api/.env  and fill it in."
fi

ok "Starting DS-Agent API on http://localhost:8000"
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload &
ML_PID=$!

deactivate

# ============================================================
#  2. WEB-APP (Next.js on :3000)
# ============================================================
log "${BOLD}Setting up web-app…${RESET}"

cd "$WEB_DIR"

# node_modules
if [ ! -d "node_modules" ]; then
  log "Installing Node dependencies (first run — this may take a minute)…"
  npm install
else
  log "Node dependencies already installed."
fi

if [ ! -f ".env.local" ]; then
  warn ".env.local not found — creating a default one."
  cat > .env.local <<'EOF'
# Fill in your real values — see ARCHITECTURE.md for details
MONGODB_URI=
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
AUTH_SECRET=
NEXTAUTH_URL=http://localhost:3000
ML_BACKEND_URL=http://localhost:8000
EOF
  warn "Please fill in .env.local and re-run this script."
  exit 1
fi

ok "Starting Next.js dev server on http://localhost:3000"
npm run dev &
WEB_PID=$!

# ============================================================
#  3. Wait / status
# ============================================================
echo ""
echo -e "${BOLD}============================================${RESET}"
echo -e "  ${GREEN}ML backend ${RESET}→ http://localhost:8000"
echo -e "  ${GREEN}Web app    ${RESET}→ http://localhost:3000"
echo -e "${BOLD}============================================${RESET}"
echo -e "  Press ${BOLD}Ctrl-C${RESET} to stop both services."
echo ""

wait "$ML_PID" "$WEB_PID"
