@echo off
setlocal EnableDelayedExpansion

:: ============================================================
::  AgentDevInsight Start Script
::  Usage: Double-click scripts\start.bat (after setup.bat)
:: ============================================================

:: Resolve absolute paths
set "SCRIPT_DIR=%~dp0"
set "PROJECT_DIR=%SCRIPT_DIR%.."
set "BACKEND_DIR=%PROJECT_DIR%\backend"
set "FRONTEND_DIR=%PROJECT_DIR%\frontend"

echo ========================================
echo  AgentDevInsight Starting...
echo ========================================
echo.

:: ---- Validate environment ----
set "READY=1"

if not exist "%BACKEND_DIR%\venv\Scripts\python.exe" (
    echo [ERROR] Backend venv not found or incomplete.
    echo.
    echo  Expected: %BACKEND_DIR%\venv\Scripts\python.exe
    echo.
    echo  Please run scripts\setup.bat first.
    echo  If setup already ran, delete the venv folder and retry.
    echo.
    set "READY=0"
)

if not exist "%FRONTEND_DIR%\node_modules" (
    echo [ERROR] Frontend node_modules not found.
    echo.
    echo  Expected: %FRONTEND_DIR%\node_modules
    echo.
    echo  Please run scripts\setup.bat first.
    echo.
    set "READY=0"
)

if "%READY%"=="0" (
    echo.
    set /p "DO_SETUP=Run setup.bat now? (Y/N): "
    if /i "!DO_SETUP!"=="Y" (
        call "%SCRIPT_DIR%setup.bat"
        if errorlevel 1 exit /b 1
        echo.
        echo Setup done, continuing to start services...
        echo.
    ) else (
        pause
        exit /b 1
    )
)

:: ---- Start services ----

echo [1/2] Starting backend (http://localhost:8000)...
start "AgentDevInsight Backend" cmd /k "cd /d "%BACKEND_DIR%" && "%BACKEND_DIR%\venv\Scripts\activate.bat" && uvicorn app.main:app --reload"

echo   Waiting for backend...
timeout /t 4 /nobreak >nul

echo [2/2] Starting frontend (http://localhost:3000)...
start "AgentDevInsight Frontend" cmd /k "cd /d "%FRONTEND_DIR%" && npm run dev"

echo.
echo ========================================
echo  Services are starting...
echo.
echo    Frontend:  http://localhost:3000
echo    Backend:   http://localhost:8000
echo    API Docs:  http://localhost:8000/docs
echo.
echo  Close the service windows to stop
echo ========================================
echo.

pause
