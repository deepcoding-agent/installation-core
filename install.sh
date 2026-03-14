#!/usr/bin/env bash
# =============================================================================
#  PrepPilot — Install dependencies (Mac / Linux)
#  Run once before start.sh:
#    bash installation-core/install.sh
# =============================================================================
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

ML_DIR="$ROOT/ml-datascience"
WEB_DIR="$ROOT/web-app"

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
CYAN='\033[0;36m'; BOLD='\033[1m'; RESET='\033[0m'

log()  { echo -e "${CYAN}[install]${RESET} $*"; }
ok()   { echo -e "${GREEN}[install]${RESET} $*"; }
warn() { echo -e "${YELLOW}[install]${RESET} $*"; }
die()  { echo -e "${RED}[install] ERROR:${RESET} $*"; exit 1; }

# ── Check prerequisites ────────────────────────────────────────────────────
command -v python3 >/dev/null 2>&1 || die "python3 not found. Install from https://python.org or run: brew install python"
command -v node    >/dev/null 2>&1 || die "node not found. Install from https://nodejs.org or run: brew install node"
command -v npm     >/dev/null 2>&1 || die "npm not found. Install Node.js from https://nodejs.org"

PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
log "Python ${PYTHON_VERSION} detected"

NODE_VERSION=$(node --version)
log "Node ${NODE_VERSION} detected"

# ── ML-Datascience ─────────────────────────────────────────────────────────
log "${BOLD}Setting up ml-datascience…${RESET}"
cd "$ML_DIR"

if [ ! -d ".venv" ]; then
  log "Creating Python virtual environment (.venv)…"
  python3 -m venv .venv
fi

source .venv/bin/activate
log "Upgrading pip…"
pip install --quiet --upgrade pip
log "Installing Python dependencies…"
pip install --quiet -r requirements.txt
log "Installing local package (pip install -e .)…"
pip install --quiet -e .
deactivate
ok "ml-datascience dependencies installed."

# ── .env file ─────────────────────────────────────────────────────────────
if [ ! -f "api/.env" ] && [ -f "api/.env.example" ]; then
  cp api/.env.example api/.env
  warn "Created ml-datascience/api/.env from .env.example — please fill in OPENAI_API_KEY."
elif [ ! -f "api/.env" ]; then
  warn "ml-datascience/api/.env not found and no .env.example to copy from."
  warn "Create ml-datascience/api/.env with: OPENAI_API_KEY=sk-..."
fi

# ── Web-App ────────────────────────────────────────────────────────────────
log "${BOLD}Setting up web-app…${RESET}"
cd "$WEB_DIR"

log "Installing Node dependencies…"
npm install
ok "web-app dependencies installed."

# ── .env.local file ───────────────────────────────────────────────────────
if [ ! -f ".env.local" ]; then
  cat > .env.local <<'EOF'
# Fill in your real values before running start.sh
MONGODB_URI=
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
AUTH_SECRET=
NEXTAUTH_URL=http://localhost:3000
ML_BACKEND_URL=http://localhost:8000
EOF
  warn "Created web-app/.env.local — please fill in all values before running start.sh."
fi

echo ""
echo -e "${BOLD}============================================${RESET}"
echo -e "  ${GREEN}Installation complete!${RESET}"
echo -e "${BOLD}============================================${RESET}"
echo -e "  Next steps:"
echo -e "  1. Fill in ${BOLD}ml-datascience/api/.env${RESET}"
echo -e "  2. Fill in ${BOLD}web-app/.env.local${RESET}"
echo -e "  3. Run:   ${BOLD}bash installation-core/start.sh${RESET}"
echo ""
