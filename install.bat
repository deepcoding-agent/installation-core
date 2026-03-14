@echo off
REM =============================================================================
REM  PrepPilot — Install dependencies (Windows)
REM  Run once before start.bat:
REM    installation-core\install.bat
REM =============================================================================
setlocal EnableDelayedExpansion

set "SCRIPT_DIR=%~dp0"
set "ROOT=%SCRIPT_DIR%.."

set "ML_DIR=%ROOT%\ml-datascience"
set "WEB_DIR=%ROOT%\web-app"

echo.
echo  [install] PrepPilot dependency installer (Windows)
echo  =====================================================
echo.

REM ── Check prerequisites ────────────────────────────────────────────────────
where python >nul 2>&1
if %ERRORLEVEL% neq 0 (
  where py >nul 2>&1
  if %ERRORLEVEL% neq 0 (
    echo  [install] ERROR: Python not found.
    echo             Install from https://www.python.org  ^(check "Add to PATH"^)
    pause & exit /b 1
  )
  set "PYTHON=py"
) else (
  set "PYTHON=python"
)

where node >nul 2>&1
if %ERRORLEVEL% neq 0 (
  echo  [install] ERROR: Node.js not found. Install from https://nodejs.org
  pause & exit /b 1
)

where npm >nul 2>&1
if %ERRORLEVEL% neq 0 (
  echo  [install] ERROR: npm not found. Install Node.js from https://nodejs.org
  pause & exit /b 1
)

for /f "tokens=*" %%v in ('%PYTHON% --version 2^>^&1') do echo  [install] %%v detected
for /f "tokens=*" %%v in ('node --version') do echo  [install] Node %%v detected

REM ── ML-Datascience ─────────────────────────────────────────────────────────
echo.
echo  [install] Setting up ml-datascience...

cd /d "%ML_DIR%"

if not exist ".venv" (
  echo  [install] Creating Python virtual environment ^(.venv^)...
  %PYTHON% -m venv .venv
)

call .venv\Scripts\activate.bat

echo  [install] Upgrading pip...
python -m pip install --quiet --upgrade pip

echo  [install] Installing Python dependencies...
pip install --quiet -r requirements.txt

echo  [install] Installing local package...
pip install --quiet -e .

call deactivate

echo  [install] ml-datascience dependencies installed.

REM ── .env file ─────────────────────────────────────────────────────────────
if not exist "api\.env" (
  if exist "api\.env.example" (
    copy "api\.env.example" "api\.env" >nul
    echo  [install] WARN: Created ml-datascience\api\.env from .env.example
    echo             Please fill in OPENAI_API_KEY before running start.bat
  ) else (
    echo  [install] WARN: ml-datascience\api\.env not found
    echo             Create it with: OPENAI_API_KEY=sk-...
  )
)

REM ── Web-App ────────────────────────────────────────────────────────────────
echo.
echo  [install] Setting up web-app...

cd /d "%WEB_DIR%"

echo  [install] Installing Node dependencies...
call npm install

echo  [install] web-app dependencies installed.

REM ── .env.local file ───────────────────────────────────────────────────────
if not exist ".env.local" (
  (
    echo # Fill in your real values before running start.bat
    echo MONGODB_URI=
    echo GOOGLE_CLIENT_ID=
    echo GOOGLE_CLIENT_SECRET=
    echo AUTH_SECRET=
    echo NEXTAUTH_URL=http://localhost:3000
    echo ML_BACKEND_URL=http://localhost:8000
  ) > .env.local
  echo  [install] WARN: Created web-app\.env.local
  echo             Please fill in all values before running start.bat
)

echo.
echo  ============================================
echo    Installation complete!
echo  ============================================
echo    Next steps:
echo    1. Fill in  ml-datascience\api\.env
echo    2. Fill in  web-app\.env.local
echo    3. Run:     installation-core\start.bat
echo.
pause
