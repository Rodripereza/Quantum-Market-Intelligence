@echo off
setlocal EnableDelayedExpansion
set ROOT=%~dp0
cd /d "%ROOT%"
title Quantum Market Intelligence Foundation v1.2 Launcher

echo ==================================================
echo      Quantum Market Intelligence Foundation v1.2
echo ==================================================
echo.

echo [1/6] Checking Python 3.12...
py -3.12 --version >nul 2>&1
if errorlevel 1 (
  echo.
  echo ERROR: Python 3.12 is not installed or is not available through the py launcher.
  echo Install Python 3.12.x and run this file again.
  echo.
  pause
  exit /b 1
)
py -3.12 --version

echo.
echo [2/6] Preparing backend virtual environment...
cd /d "%ROOT%backend"
if not exist ".venv\Scripts\python.exe" (
  py -3.12 -m venv .venv
)
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt
if errorlevel 1 (
  echo.
  echo ERROR: Backend dependency installation failed.
  pause
  exit /b 1
)

echo.
echo [3/6] Starting FastAPI backend...
start "QMI Backend Foundation v1.2" cmd /k "cd /d "%ROOT%backend" && call .venv\Scripts\activate.bat && uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload"

echo.
echo [4/6] Waiting for backend health check...
set BACKEND_OK=0
for /l %%i in (1,1,30) do (
  powershell -NoProfile -ExecutionPolicy Bypass -Command "try { $r = Invoke-WebRequest -Uri 'http://127.0.0.1:8000/health' -UseBasicParsing -TimeoutSec 2; if ($r.StatusCode -eq 200) { exit 0 } else { exit 1 } } catch { exit 1 }" >nul 2>&1
  if !errorlevel! equ 0 (
    set BACKEND_OK=1
    goto backend_ready
  )
  timeout /t 1 >nul
)
:backend_ready
if "%BACKEND_OK%"=="0" (
  echo.
  echo ERROR: Backend did not respond at http://127.0.0.1:8000/health
  echo Check the QMI Backend window for details.
  pause
  exit /b 1
)
echo Backend OK.

echo.
echo [5/6] Preparing frontend...
cd /d "%ROOT%frontend"
where npm >nul 2>&1
if errorlevel 1 (
  echo.
  echo ERROR: Node.js / npm is not installed.
  echo Install Node.js LTS and run this file again.
  pause
  exit /b 1
)
if not exist "node_modules" (
  npm install
  if errorlevel 1 (
    echo.
    echo ERROR: Frontend dependency installation failed.
    pause
    exit /b 1
  )
)

echo.
echo [6/6] Starting React frontend...
start "QMI Frontend Foundation v1.2" cmd /k "cd /d "%ROOT%frontend" && npm run dev -- --host 127.0.0.1"
timeout /t 4 >nul
start http://127.0.0.1:5173

echo.
echo QMI Foundation v1.2 launched.
echo Backend:  http://127.0.0.1:8000/health
echo Frontend: http://127.0.0.1:5173
echo.
pause
