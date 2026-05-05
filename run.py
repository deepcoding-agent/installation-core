#!/usr/bin/env python3
"""
PrepPilot — single-command launcher (Mac / Linux / Windows)

Usage:
    python installation-core/run.py              # install deps + start (no Docker)
    python installation-core/run.py --docker     # start with Docker (recommended for sharing)
    python installation-core/run.py --docker-build  # rebuild images + start
    python installation-core/run.py --docker-down   # stop Docker services
    python installation-core/run.py --install    # install deps only (no start)
    python installation-core/run.py --start      # start only (skip install checks)
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

# ── Paths ─────────────────────────────────────────────────────────────────────
SCRIPT_DIR = Path(__file__).resolve().parent   # installation-core/
ROOT       = SCRIPT_DIR.parent                 # seniorproject/
ML_DIR     = ROOT / "ml-datascience"
WEB_DIR    = ROOT / "web-app"
COMPOSE    = SCRIPT_DIR / "docker-compose.yml"

IS_WINDOWS = platform.system() == "Windows"
PYTHON     = sys.executable

if IS_WINDOWS:
    VENV_PYTHON = ML_DIR / ".venv" / "Scripts" / "python.exe"
    VENV_PIP    = ML_DIR / ".venv" / "Scripts" / "pip.exe"
else:
    VENV_PYTHON = ML_DIR / ".venv" / "bin" / "python"
    VENV_PIP    = ML_DIR / ".venv" / "bin" / "pip"

# ── Colors ────────────────────────────────────────────────────────────────────
_USE_COLOR = not IS_WINDOWS or os.environ.get("WT_SESSION") or os.environ.get("ANSICON")

def _c(code: str, text: str) -> str:
    return f"\033[{code}m{text}\033[0m" if _USE_COLOR else text

def log(msg: str)  -> None: print(_c("36", "[run]") + " " + msg)
def ok(msg: str)   -> None: print(_c("32", "[run]") + " " + msg)
def warn(msg: str) -> None: print(_c("33", "[run]") + " " + msg)
def die(msg: str)  -> None: print(_c("31", "[run] ERROR:") + " " + msg); sys.exit(1)

def banner(msg: str) -> None:
    line = "=" * 48
    print(f"\n  {line}")
    print(f"  {msg}")
    print(f"  {line}\n")

# ── Helpers ───────────────────────────────────────────────────────────────────

def require_cmd(cmd: str, install_hint: str) -> None:
    if shutil.which(cmd) is None:
        die(f"'{cmd}' not found. {install_hint}")

def run(args: list[str], **kwargs) -> subprocess.CompletedProcess:
    return subprocess.run(args, check=True, **kwargs)

def load_env_file(path: Path) -> dict[str, str]:
    env: dict[str, str] = {}
    if not path.exists():
        return env
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        v = v.strip().strip('"').strip("'")   # remove surrounding quotes
        env[k.strip()] = v
    return env

def create_env_from_example(example: Path, dest: Path) -> None:
    if example.exists():
        shutil.copy(example, dest)
        warn(f"Created {dest.relative_to(ROOT)} from example — fill in your values.")
    else:
        dest.write_text("# Fill in values\n", encoding="utf-8")
        warn(f"Created empty {dest.relative_to(ROOT)} — fill in your values.")

# ── Repo URLs ─────────────────────────────────────────────────────────────────

REPOS = {
    WEB_DIR: "https://github.com/deepcoding-agent/web-app.git",
    ML_DIR:  "https://github.com/deepcoding-agent/ml-datascience.git",
}

# ── Repo presence check & auto-clone ─────────────────────────────────────────

def check_repos() -> None:
    """Clone sibling repos if they are missing."""
    require_cmd("git", "Install git from https://git-scm.com")

    for dest, url in REPOS.items():
        if dest.exists():
            continue
        log(f"Cloning {url} → {dest.name}/")
        try:
            run(["git", "clone", url, str(dest)])
            ok(f"{dest.name}/ cloned.")
        except subprocess.CalledProcessError:
            die(f"Failed to clone {url}\nCheck your internet connection or repo access.")

# ── Prerequisite checks ───────────────────────────────────────────────────────

def check_prerequisites(need_docker: bool = False) -> None:
    log("Checking prerequisites…")

    if sys.version_info < (3, 10):
        die(f"Python 3.10+ required. You have {sys.version}.")

    if need_docker:
        require_cmd("docker", "Install Docker Desktop from https://docker.com")
        try:
            subprocess.run(["docker", "info"], capture_output=True, check=True)
        except subprocess.CalledProcessError:
            die("Docker daemon is not running. Start Docker Desktop first.")
        ok("Docker is running.")
    else:
        require_cmd("node", "Install Node.js 18+ from https://nodejs.org")
        require_cmd("npm",  "Install Node.js 18+ from https://nodejs.org")
        py_ver   = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        node_ver = subprocess.check_output(["node", "--version"], text=True).strip()
        npm_ver  = subprocess.check_output(["npm",  "--version"], text=True).strip()
        ok(f"Python {py_ver}  |  Node {node_ver}  |  npm {npm_ver}")

# ── Placeholder detection ─────────────────────────────────────────────────────

# Values copied straight from .env.example that haven't been replaced
_PLACEHOLDERS = {
    "your-google-client-id",
    "your-client-id",
    "your-google-client-secret",
    "your-client-secret",
    "your-random-secret",
    "your-random-secret-here",
    "sk-...",
    "sk-proj-",
}

def _is_placeholder(value: str) -> bool:
    v = value.strip().lower()
    return not v or any(p in v for p in _PLACEHOLDERS)

# ── Environment file checks ───────────────────────────────────────────────────

def check_env_files() -> bool:
    ready = True

    # ── ml-datascience/api/.env ───────────────────────────────────────────────
    ml_env = ML_DIR / "api" / ".env"
    if not ml_env.exists():
        create_env_from_example(ML_DIR / "api" / ".env.example", ml_env)
        ready = False
    else:
        ml_vals = load_env_file(ml_env)
        key = ml_vals.get("OPENAI_API_KEY", "")
        if not key.strip():
            warn("OPENAI_API_KEY is empty in ml-datascience/api/.env")
            ready = False
        elif _is_placeholder(key):
            warn("OPENAI_API_KEY still has a placeholder value — replace it with your real key")
            ready = False

    # ── web-app/.env.local ────────────────────────────────────────────────────
    web_env = WEB_DIR / ".env.local"
    if not web_env.exists():
        create_env_from_example(WEB_DIR / ".env.local.example", web_env)
        ready = False
    else:
        web_vals = load_env_file(web_env)

        required_keys = (
            "GOOGLE_CLIENT_ID",
            "GOOGLE_CLIENT_SECRET",
            "AUTH_SECRET",
            "NEXTAUTH_URL",
            "DATABASE_URL",
        )
        for k in required_keys:
            v = web_vals.get(k, "")
            if not v.strip():
                warn(f"{k} is missing from web-app/.env.local")
                ready = False
            elif _is_placeholder(v):
                warn(f"{k} still has a placeholder value in web-app/.env.local — fill in the real value")
                ready = False

    if not ready:
        print()
        print("  Fill in all missing values, then re-run:")
        print(f"    {_c('1', 'python installation-core/run.py')}")
        print()

    return ready

# ── Docker commands ───────────────────────────────────────────────────────────

def docker_up(build: bool = False) -> None:
    check_prerequisites(need_docker=True)
    if not check_env_files():
        sys.exit(1)

    # Windows WSL2 check
    if IS_WINDOWS:
        try:
            info = subprocess.check_output(
                ["docker", "info", "--format", "{{.OSType}}"],
                text=True, stderr=subprocess.DEVNULL,
            ).strip()
            if info == "linux":
                ok("Docker Desktop with WSL 2 backend detected.")
        except Exception:
            pass

    banner("PrepPilot — Docker")

    # Set COMPOSE_CONVERT_WINDOWS_PATHS for Docker Compose V1 compat
    env = os.environ.copy()
    if IS_WINDOWS:
        env["COMPOSE_CONVERT_WINDOWS_PATHS"] = "1"

    cmd = ["docker", "compose", "-f", str(COMPOSE), "up"]
    if build:
        cmd.append("--build")

    print(f"  {_c('32', 'ML backend')}  →  http://localhost:8000")
    print(f"  {_c('32', 'Web app')}     →  http://localhost:3000")
    print(f"  {_c('32', 'API docs')}    →  http://localhost:8000/docs")
    print(f"\n  Hot reload is ON — edit code on your machine,")
    print(f"  changes apply automatically inside containers.")
    print(f"\n  Press {_c('1', 'Ctrl-C')} to stop.\n")

    try:
        subprocess.run(cmd, cwd=str(SCRIPT_DIR), env=env, check=True)
    except KeyboardInterrupt:
        pass

def docker_down() -> None:
    log("Stopping Docker services…")
    env = os.environ.copy()
    if IS_WINDOWS:
        env["COMPOSE_CONVERT_WINDOWS_PATHS"] = "1"
    subprocess.run(
        ["docker", "compose", "-f", str(COMPOSE), "down"],
        cwd=str(SCRIPT_DIR),
        env=env,
    )
    ok("All Docker services stopped.")

# ── Local (non-Docker) launchers ──────────────────────────────────────────────

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
    ok("Python dependencies ready.")

def install_node_deps() -> None:
    if not (WEB_DIR / "node_modules").exists():
        log("Installing Node dependencies (first run — may take a minute)…")
        run(["npm", "install"], cwd=str(WEB_DIR))
    else:
        log("Node dependencies already installed.")
    ok("Node dependencies ready.")

def install_all() -> None:
    log("─── Installing dependencies ───")
    install_python_deps()
    install_node_deps()

def _ml_env() -> dict[str, str]:
    env = os.environ.copy()
    env.update(load_env_file(ML_DIR / "api" / ".env"))
    return env

def start_services() -> None:
    banner("PrepPilot — starting services (local)")

    if not VENV_PYTHON.exists():
        die("Python virtual environment not found. Run without --start first.")
    if not (WEB_DIR / "node_modules").exists():
        die("Node modules not found. Run without --start first.")

    uvicorn_args = [
        str(VENV_PYTHON), "-m", "uvicorn",
        "api.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload",
    ]
    npm_args = ["npm.cmd", "run", "dev"] if IS_WINDOWS else ["npm", "run", "dev"]

    # Windows: CREATE_NEW_PROCESS_GROUP lets us send CTRL_BREAK_EVENT to each process
    # Unix: start_new_session=True creates a new process group so killpg works
    popen_kwargs_ml  = {"cwd": str(ML_DIR), "env": _ml_env()}
    popen_kwargs_web = {"cwd": str(WEB_DIR)}
    if IS_WINDOWS:
        popen_kwargs_ml["creationflags"]  = subprocess.CREATE_NEW_PROCESS_GROUP
        popen_kwargs_web["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
    else:
        popen_kwargs_ml["start_new_session"]  = True
        popen_kwargs_web["start_new_session"] = True

    log("Starting PrepPilot API  →  http://localhost:8000")
    ml_proc = subprocess.Popen(uvicorn_args, **popen_kwargs_ml)

    log("Starting Next.js dev server  →  http://localhost:3000")
    web_proc = subprocess.Popen(npm_args, **popen_kwargs_web)

    procs = [ml_proc, web_proc]

    print()
    print(_c("1", "  ══════════════════════════════════════════════"))
    print(f"  {_c('32', 'ML backend')}  →  http://localhost:8000")
    print(f"  {_c('32', 'Web app')}     →  http://localhost:3000")
    print(_c("1", "  ══════════════════════════════════════════════"))
    print(f"  Press {_c('1', 'Ctrl-C')} to stop both services.")
    print()

    def _shutdown(signum=None, frame=None) -> None:
        print()
        log("Shutting down…")
        for p in procs:
            try:
                if IS_WINDOWS:
                    # CTRL_BREAK_EVENT propagates to the process group we created
                    p.send_signal(signal.CTRL_BREAK_EVENT)
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

    signal.signal(signal.SIGINT, _shutdown)
    try:
        signal.signal(signal.SIGTERM, _shutdown)
    except (OSError, ValueError):
        pass   # SIGTERM registration unsupported on some Windows configurations

    while True:
        for p in procs:
            ret = p.poll()
            if ret is not None:
                name = "ML backend" if p is ml_proc else "Web app"
                warn(f"{name} exited (code {ret}). Stopping all…")
                _shutdown()
        time.sleep(1)

# ── Entry point ───────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="PrepPilot — install and start all services."
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--docker",       action="store_true", help="Start with Docker (no rebuild)")
    group.add_argument("--docker-build", action="store_true", help="Rebuild Docker images and start")
    group.add_argument("--docker-down",  action="store_true", help="Stop Docker services")
    group.add_argument("--install",      action="store_true", help="Install local deps only")
    group.add_argument("--start",        action="store_true", help="Start local services (skip install)")
    args = parser.parse_args()

    banner("PrepPilot  run.py")

    check_repos()   # fail fast if sibling repos are missing

    if args.docker_down:
        docker_down()
        return

    if args.docker:
        docker_up(build=False)
        return

    if args.docker_build:
        docker_up(build=True)
        return

    # ── Local (non-Docker) path ───────────────────────────────────────────────
    check_prerequisites(need_docker=False)

    if args.start:
        if not check_env_files():
            sys.exit(1)
        start_services()
        return

    if args.install:
        install_all()
        check_env_files()
        ok("Done. Fill in any missing env values, then: python installation-core/run.py")
        return

    # Default: install + check + start
    install_all()
    if not check_env_files():
        sys.exit(1)
    start_services()


if __name__ == "__main__":
    main()
