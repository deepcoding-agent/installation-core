#!/usr/bin/env bash
# =============================================================================
# install.sh — Install dependencies for web-app and ml-datascience
# =============================================================================
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

info()    { echo -e "${GREEN}[install]${NC} $*"; }
warning() { echo -e "${YELLOW}[warning]${NC} $*"; }
error()   { echo -e "${RED}[error]${NC} $*"; exit 1; }

# =============================================================================
# 1. web-app (Next.js / Node)
# =============================================================================
info "Installing web-app dependencies..."

cd "$SCRIPT_DIR/web-app"

if ! command -v node &>/dev/null; then
  error "Node.js is not installed. Install it from https://nodejs.org (v18+ recommended)."
fi

NODE_VERSION=$(node -v | sed 's/v//' | cut -d. -f1)
if [ "$NODE_VERSION" -lt 18 ]; then
  warning "Node.js v$NODE_VERSION detected. v18 or higher is recommended."
fi

npm install

if [ ! -f ".env.local" ]; then
  if [ -f ".env.local.example" ]; then
    cp .env.local.example .env.local
    warning "Created web-app/.env.local from .env.local.example — fill in your secrets before running."
  else
    warning "web-app/.env.local not found. Create it with the required environment variables."
  fi
fi

info "web-app dependencies installed."

# =============================================================================
# 2. ml-datascience (Python / FastAPI)
# =============================================================================
info "Installing ml-datascience dependencies..."

cd "$SCRIPT_DIR/ml-datascience"

if ! command -v python3 &>/dev/null; then
  error "Python 3 is not installed. Install it from https://python.org (v3.10+ recommended)."
fi

PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
PYTHON_MAJOR=$(echo "$PYTHON_VERSION" | cut -d. -f1)
PYTHON_MINOR=$(echo "$PYTHON_VERSION" | cut -d. -f2)
if [ "$PYTHON_MAJOR" -lt 3 ] || { [ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 10 ]; }; then
  warning "Python $PYTHON_VERSION detected. Python 3.10 or higher is recommended."
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
  info "Creating Python virtual environment at ml-datascience/venv..."
  python3 -m venv venv
fi

# Activate venv
source venv/bin/activate

info "Upgrading pip..."
pip install --upgrade pip --quiet

info "Installing Python packages from requirements.txt..."
pip install -r requirements.txt --quiet

info "Installing ml-datascience package in editable mode..."
pip install -e . --quiet

if [ ! -f ".env" ]; then
  cat > .env << 'EOF'
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4o-mini
EOF
  warning "Created ml-datascience/.env — add your OPENAI_API_KEY before running."
fi

deactivate

info "ml-datascience dependencies installed."

# =============================================================================
# Done
# =============================================================================
echo ""
echo -e "${GREEN}============================================${NC}"
echo -e "${GREEN}  All dependencies installed successfully!${NC}"
echo -e "${GREEN}============================================${NC}"
echo ""
echo "  Start web-app:        cd web-app && npm run dev"
echo "  Start ml-datascience: cd ml-datascience && source venv/bin/activate && uvicorn api.main:app --reload --port 8000"
echo ""
echo "  Make sure to fill in your .env files before running."
echo ""
