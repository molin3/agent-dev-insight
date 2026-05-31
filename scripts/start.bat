@echo off
setlocal

:: Resolve project root directory
set "PROJECT_DIR=%~dp0.."

echo ========================================
echo  AgentDevInsight Starting...
echo ========================================
echo.

:: Check venv exists
if not exist "%PROJECT_DIR%\backend\venv\Scripts\python.exe" (
    echo [ERROR] Backend virtual environment not found.
    echo.
    echo  The venv directory exists but is incomplete, or setup.bat
    echo  was never run. Please run scripts\setup.bat first.
    echo.
    echo  If setup.bat already ran, try:
    echo    1. Delete the folder: %PROJECT_DIR%\backend\venv
    echo    2. Run scripts\setup.bat again
    echo.
    pause
    exit /b 1
)

:: Check node_modules exists
if not exist "%PROJECT_DIR%\frontend\node_modules" (
    echo [ERROR] Frontend dependencies not found.
    echo.
    echo  Please run scripts\setup.bat first.
    echo.
    pause
    exit /b 1
)

:: Start backend in new window
echo [1/2] Starting backend (http://localhost:8000)...
start "AgentDevInsight Backend" cmd /k "cd /d "%PROJECT_DIR%\backend" && call venv\Scripts\activate.bat && uvicorn app.main:app --reload"

:: Wait for backend to start
echo   Waiting for backend to initialize...
timeout /t 4 /nobreak >nul

:: Start frontend in new window
echo [2/2] Starting frontend (http://localhost:3000)...
start "AgentDevInsight Frontend" cmd /k "cd /d "%PROJECT_DIR%\frontend" && npm run dev"

echo.
echo ========================================
echo  Services are starting...
echo.
echo  Frontend:  http://localhost:3000
echo  Backend:   http://localhost:8000
echo  API Docs:  http://localhost:8000/docs
echo.
echo  Close the service windows to stop them
echo ========================================
echo.

pause
