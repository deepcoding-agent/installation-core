@echo off
REM =============================================================================
REM  PrepPilot — One-command launcher (Windows)
REM  Run from anywhere:
REM    installation-core\start.bat
REM =============================================================================
setlocal EnableDelayedExpansion

set "SCRIPT_DIR=%~dp0"
set "ROOT=%SCRIPT_DIR%.."

set "ML_DIR=%ROOT%\ml-datascience"
set "WEB_DIR=%ROOT%\web-app"

echo.
echo  [launch] PrepPilot launcher (Windows)
echo  ======================================
echo.

REM ── Check prerequisites ────────────────────────────────────────────────────
where python >nul 2>&1
if %ERRORLEVEL% neq 0 (
  where py >nul 2>&1
  if %ERRORLEVEL% neq 0 (
    echo  [launch] ERROR: Python not found. Run install.bat first.
    pause & exit /b 1
  )
  set "PYTHON=py"
) else (
  set "PYTHON=python"
)

where node >nul 2>&1
if %ERRORLEVEL% neq 0 (
  echo  [launch] ERROR: Node.js not found. Run install.bat first.
  pause & exit /b 1
)

REM ── Check .env files ──────────────────────────────────────────────────────
if not exist "%ML_DIR%\api\.env" (
  echo  [launch] ERROR: ml-datascience\api\.env not found.
  echo           Run install.bat first, then fill in your API keys.
  pause & exit /b 1
)

if not exist "%WEB_DIR%\.env.local" (
  echo  [launch] ERROR: web-app\.env.local not found.
  echo           Run install.bat first, then fill in your environment variables.
  pause & exit /b 1
)

REM ── Validate OPENAI_API_KEY ───────────────────────────────────────────────
for /f "usebackq tokens=1,* delims==" %%a in ("%ML_DIR%\api\.env") do (
  if "%%a"=="OPENAI_API_KEY" set "OPENAI_API_KEY=%%b"
)
if "!OPENAI_API_KEY!"=="" (
  echo  [launch] ERROR: OPENAI_API_KEY is not set in ml-datascience\api\.env
  pause & exit /b 1
)

REM ── Check virtual environment ─────────────────────────────────────────────
if not exist "%ML_DIR%\.venv\Scripts\activate.bat" (
  echo  [launch] ERROR: Python virtual environment not found.
  echo           Run install.bat first.
  pause & exit /b 1
)

REM ── Check node_modules ───────────────────────────────────────────────────
if not exist "%WEB_DIR%\node_modules" (
  echo  [launch] ERROR: web-app\node_modules not found.
  echo           Run install.bat first.
  pause & exit /b 1
)

REM ── Launch ML backend in a new window ─────────────────────────────────────
echo  [launch] Starting DS-Agent API on http://localhost:8000 ...
start "PrepPilot - ML Backend" cmd /k "cd /d "%ML_DIR%" && call .venv\Scripts\activate.bat && uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload"

REM ── Wait a moment for the backend to start ────────────────────────────────
timeout /t 3 /nobreak >nul

REM ── Launch Web App in a new window ────────────────────────────────────────
echo  [launch] Starting Next.js dev server on http://localhost:3000 ...
start "PrepPilot - Web App" cmd /k "cd /d "%WEB_DIR%" && npm run dev"

echo.
echo  ============================================
echo    ML backend  -^>  http://localhost:8000
echo    Web app     -^>  http://localhost:3000
echo  ============================================
echo    Both services are running in separate windows.
echo    Close those windows (or press Ctrl-C in them) to stop.
echo.
pause
