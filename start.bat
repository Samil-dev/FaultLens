@echo off
REM Launches the FaultLens backend and frontend, each in its own window,
REM then opens the dashboard in your default browser.

setlocal
set "ROOT=%~dp0"

echo ============================================
echo   FaultLens - starting backend + frontend
echo ============================================

echo.
echo [1/3] Starting backend (FastAPI, port 8000)...
start "FaultLens Backend" cmd /k "cd /d "%ROOT%Backend" && venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000"

echo [2/3] Waiting for backend to boot...
timeout /t 3 /nobreak >nul

echo [3/3] Starting frontend (Vite, port 3000)...
start "FaultLens Frontend" cmd /k "cd /d "%ROOT%Frontend" && npm run dev"

echo.
echo Waiting for frontend to boot...
timeout /t 4 /nobreak >nul

echo Opening http://localhost:3000 ...
start "" "http://localhost:3000"

echo.
echo Two windows were opened: "FaultLens Backend" and "FaultLens Frontend".
echo Close them (or Ctrl+C inside each) to stop the servers.
echo If the backend window shows a "port already in use" error, it means
echo a backend instance was already running - that's fine, it's still serving.
echo.
endlocal
