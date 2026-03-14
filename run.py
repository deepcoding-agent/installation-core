#!/usr/bin/env python3
"""
PrepPilot — single-command launcher (Mac / Linux / Windows)

Usage:
    python installation-core/run.py          # install deps if needed, then start
    python installation-core/run.py --start  # start only (skip install checks)
    python installation-core/run.py --install # install only (no start)
"""
from __future__ import annotations

import argparse
import os
import platform
import shutil
import signal
import subprocess
import sys
import time
from pathlib import Path

# ── Paths ────────────────────────────────────────────────────────────────────
SCRIPT_DIR = Path(__file__).resolve().parent
ROOT       = SCRIPT_DIR.parent
ML_DIR     = ROOT / "ml-datascience"
WEB_DIR    = ROOT / "web-app"

IS_WINDOWS = platform.system() == "Windows"
PYTHON     = sys.executable  # same interpreter that is running this script

# venv python / pip paths differ between platforms
if IS_WINDOWS:
    VENV_PYTHON = ML_DIR / ".venv" / "Scripts" / "python.exe"
    VENV_PIP    = ML_DIR / ".venv" / "Scripts" / "pip.exe"
else:
    VENV_PYTHON = ML_DIR / ".venv" / "bin" / "python"
    VENV_PIP    = ML_DIR / ".venv" / "bin" / "pip"

# ── Colors (disabled on Windows cmd unless ANSICON / WT) ─────────────────────
_USE_COLOR = not IS_WINDOWS or os.environ.get("WT_SESSION") or os.environ.get("ANSICON")

def _c(code: str, text: str) -> str:
    return f"\033[{code}m{text}\033[0m" if _USE_COLOR else text

def log(msg: str)  -> None: print(_c("36", "[run]") + " " + msg)
def ok(msg: str)   -> None: print(_c("32", "[run]") + " " + msg)
def warn(msg: str) -> None: print(_c("33", "[run]") + " " + msg)
def die(msg: str)  -> None: print(_c("31", "[run] ERROR:") + " " + msg); sys.exit(1)
def banner(msg: str) -> None:
    line = "=" * 46
    print(f"\n  {line}")
    print(f"  {msg}")
    print(f"  {line}\n")

# ── Helpers ───────────────────────────────────────────────────────────────────

def require_cmd(cmd: str, install_hint: str) -> None:
    if shutil.which(cmd) is None:
        die(f"'{cmd}' not found. {install_hint}")

def run(args: list[str], **kwargs) -> subprocess.CompletedProcess:
    """Run a command, raise on failure."""
    return subprocess.run(args, check=True, **kwargs)

def load_env_file(path: Path) -> dict[str, str]:
    """Parse key=value lines from a .env file (ignores comments and blanks)."""
    env: dict[str, str] = {}
    if not path.exists():
        return env
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        env[k.strip()] = v.strip()
    return env

def create_env_template(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")
    warn(f"Created {path.relative_to(ROOT)} — fill in your values before starting.")

# ── Prerequisite checks ───────────────────────────────────────────────────────

def check_prerequisites() -> None:
    log("Checking prerequisites…")

    # Python version (already running, but check it's 3.10+)
    if sys.version_info < (3, 10):
        die(f"Python 3.10+ required. You have {sys.version}. Install from https://python.org")

    require_cmd("node", "Install Node.js 18+ from https://nodejs.org")
    require_cmd("npm",  "Install Node.js 18+ from https://nodejs.org")

    py_ver   = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    node_ver = subprocess.check_output(["node", "--version"], text=True).strip()
    npm_ver  = subprocess.check_output(["npm",  "--version"], text=True).strip()

    ok(f"Python {py_ver}  |  Node {node_ver}  |  npm {npm_ver}")

# ── Environment file checks ───────────────────────────────────────────────────

def check_env_files() -> bool:
    """
    Ensure both .env files exist with non-empty required keys.
    Returns True if everything is ready, False if the user still needs to fill something in.
    """
    ready = True

    # ── ml-datascience/api/.env ───────────────────────────────────────────────
    ml_env = ML_DIR / "api" / ".env"
    ml_example = ML_DIR / "api" / ".env.example"

    if not ml_env.exists():
        if ml_example.exists():
            shutil.copy(ml_example, ml_env)
            warn("Created ml-datascience/api/.env from .env.example")
        else:
            create_env_template(ml_env, "OPENAI_API_KEY=\nOPENAI_MODEL=gpt-4o-mini\n")
        ready = False
    else:
        ml_vals = load_env_file(ml_env)
        if not ml_vals.get("OPENAI_API_KEY", "").strip():
            warn("OPENAI_API_KEY is empty in ml-datascience/api/.env")
            ready = False

    # ── web-app/.env.local ────────────────────────────────────────────────────
    web_env = WEB_DIR / ".env.local"

    if not web_env.exists():
        create_env_template(web_env, (
            "# Fill in all values before running\n"
            "MONGODB_URI=\n"
            "GOOGLE_CLIENT_ID=\n"
            "GOOGLE_CLIENT_SECRET=\n"
            "AUTH_SECRET=\n"
            "NEXTAUTH_URL=http://localhost:3000\n"
            "ML_BACKEND_URL=http://localhost:8000\n"
        ))
        ready = False
    else:
        web_vals = load_env_file(web_env)
        missing = [k for k in ("MONGODB_URI", "GOOGLE_CLIENT_ID", "GOOGLE_CLIENT_SECRET", "AUTH_SECRET")
                   if not web_vals.get(k, "").strip()]
        if missing:
            warn(f"Missing values in web-app/.env.local: {', '.join(missing)}")
            ready = False

    if not ready:
        print()
        print("  Fill in the missing environment values, then re-run:")
        print(f"    {_c('1', 'python installation-core/run.py')}")
        print()

    return ready

# ── Dependency installation ───────────────────────────────────────────────────

def install_python_deps() -> None:
    venv_dir = ML_DIR / ".venv"

    if not venv_dir.exists():
        log("Creating Python virtual environment (.venv)…")
        run([PYTHON, "-m", "venv", str(venv_dir)])
    else:
        log("Python virtual environment already exists.")

    log("Installing / verifying Python dependencies…")
    run([str(VENV_PIP), "install", "--quiet", "--upgrade", "pip"])
    run([str(VENV_PIP), "install", "--quiet", "-r", str(ML_DIR / "requirements.txt")])
    run([str(VENV_PIP), "install", "--quiet", "-e", str(ML_DIR)])
    ok("Python dependencies ready.")

def install_node_deps() -> None:
    node_modules = WEB_DIR / "node_modules"
    if not node_modules.exists():
        log("Installing Node dependencies (first run — may take a minute)…")
        run(["npm", "install"], cwd=str(WEB_DIR))
    else:
        log("Node dependencies already installed.")
    ok("Node dependencies ready.")

def install_all() -> None:
    log("─── Installing dependencies ───")
    install_python_deps()
    install_node_deps()

# ── Service launchers ─────────────────────────────────────────────────────────

def _ml_env() -> dict[str, str]:
    """Merge current environment with ml-datascience/api/.env values."""
    env = os.environ.copy()
    env.update(load_env_file(ML_DIR / "api" / ".env"))
    return env

def start_services() -> None:
    banner("PrepPilot — starting services")

    if not VENV_PYTHON.exists():
        die("Python virtual environment not found. Run without --start first to install deps.")

    if not (WEB_DIR / "node_modules").exists():
        die("Node modules not found. Run without --start first to install deps.")

    uvicorn_args: list[str]
    if IS_WINDOWS:
        uvicorn_args = [
            str(VENV_PYTHON), "-m", "uvicorn",
            "api.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload",
        ]
        npm_args = ["npm.cmd", "run", "dev"]
    else:
        uvicorn_args = [
            str(VENV_PYTHON), "-m", "uvicorn",
            "api.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload",
        ]
        npm_args = ["npm", "run", "dev"]

    log("Starting DS-Agent API  →  http://localhost:8000")
    ml_proc = subprocess.Popen(
        uvicorn_args,
        cwd=str(ML_DIR),
        env=_ml_env(),
    )

    log("Starting Next.js dev server  →  http://localhost:3000")
    web_proc = subprocess.Popen(
        npm_args,
        cwd=str(WEB_DIR),
    )

    procs = [ml_proc, web_proc]

    print()
    print(_c("1", "  ══════════════════════════════════════════"))
    print(f"  {_c('32', 'ML backend')}  →  http://localhost:8000")
    print(f"  {_c('32', 'Web app')}     →  http://localhost:3000")
    print(_c("1", "  ══════════════════════════════════════════"))
    print(f"  Press {_c('1', 'Ctrl-C')} to stop both services.")
    print()

    # ── Graceful shutdown on Ctrl-C ───────────────────────────────────────────
    def _shutdown(signum=None, frame=None) -> None:
        print()
        log("Shutting down…")
        for p in procs:
            try:
                if IS_WINDOWS:
                    p.terminate()
                else:
                    os.killpg(os.getpgid(p.pid), signal.SIGTERM)
            except Exception:
                try:
                    p.terminate()
                except Exception:
                    pass
        for p in procs:
            try:
                p.wait(timeout=5)
            except Exception:
                p.kill()
        ok("All services stopped.")
        sys.exit(0)

    signal.signal(signal.SIGINT,  _shutdown)
    signal.signal(signal.SIGTERM, _shutdown)

    # ── Watch both processes ──────────────────────────────────────────────────
    while True:
        for p in procs:
            ret = p.poll()
            if ret is not None:
                name = "ML backend" if p is ml_proc else "Web app"
                warn(f"{name} exited with code {ret}. Stopping all services…")
                _shutdown()
        time.sleep(1)

# ── Entry point ───────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="PrepPilot — install dependencies and start both services."
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--install", action="store_true", help="Install deps only, do not start")
    group.add_argument("--start",   action="store_true", help="Start services only, skip install")
    args = parser.parse_args()

    banner("PrepPilot  run.py")

    check_prerequisites()

    if args.start:
        # Start only — still check env files
        if not check_env_files():
            sys.exit(1)
        start_services()
        return

    if args.install:
        install_all()
        check_env_files()
        ok("Done. Fill in any missing env values, then run:  python installation-core/run.py")
        return

    # Default: install (if needed) + check envs + start
    install_all()
    if not check_env_files():
        sys.exit(1)
    start_services()


if __name__ == "__main__":
    main()
