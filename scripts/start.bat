@echo off
setlocal

echo ========================================
echo  AgentDevInsight Starting...
echo ========================================
echo.

:: Check venv exists
if not exist "%~dp0..\backend\venv" (
    echo [ERROR] Backend venv not found. Run scripts\setup.bat first.
    pause
    exit /b 1
)

:: Check node_modules exists
if not exist "%~dp0..\frontend\node_modules" (
    echo [ERROR] Frontend deps not found. Run scripts\setup.bat first.
    pause
    exit /b 1
)

:: Start backend in new window
echo [1/2] Starting backend (http://localhost:8000)...
set "BACKEND_DIR=%~dp0..\backend"
start "AgentDevInsight Backend" cmd /k "cd /d "%BACKEND_DIR%" && call venv\Scripts\activate.bat && uvicorn app.main:app --reload"

:: Wait for backend to start
echo   Waiting for backend...
timeout /t 3 /nobreak >nul

:: Start frontend in new window
echo [2/2] Starting frontend (http://localhost:3000)...
set "FRONTEND_DIR=%~dp0..\frontend"
start "AgentDevInsight Frontend" cmd /k "cd /d "%FRONTEND_DIR%" && npm run dev"

echo.
echo ========================================
echo  Services started!
echo  Frontend:  http://localhost:3000
echo  Backend:   http://localhost:8000
echo  API Docs:  http://localhost:8000/docs
echo.
echo  Close the windows to stop services
echo ========================================
echo.

pause
