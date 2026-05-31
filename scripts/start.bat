@echo off
setlocal

:: ============================================================
::  AgentDevInsight Start
::  Run AFTER setup.bat has completed successfully
:: ============================================================

set "PROJECT=%~dp0.."
set "BACKEND=%PROJECT%backend"
set "FRONTEND=%PROJECT%frontend"

echo.
echo ========================================
echo  AgentDevInsight Start
echo ========================================
echo.

:: ============================================
:: Validate
:: ============================================
set "READY=1"

if not exist "%BACKEND%\venv\Scripts\python.exe" (
    echo [ERROR] Backend venv not found.
    echo   Expected: %BACKEND%\venv\Scripts\python.exe
    echo   Solution: Run scripts\setup.bat first.
    echo.
    set "READY=0"
)

if not exist "%FRONTEND%\node_modules" (
    echo [ERROR] Frontend node_modules not found.
    echo   Expected: %FRONTEND%\node_modules
    echo   Solution: Run scripts\setup.bat first.
    echo.
    set "READY=0"
)

if "%READY%"=="0" (
    goto :end
)

:: ============================================
:: Start backend
:: ============================================
echo [1/2] Starting backend...
echo   http://localhost:8000
echo   http://localhost:8000/docs
echo.

start "AgentDevInsight Backend" cmd /k "cd /d "%BACKEND%" && "%BACKEND%\venv\Scripts\activate.bat" && uvicorn app.main:app --reload"

echo   Waiting for backend to initialize...
timeout /t 4 /nobreak >nul

:: ============================================
:: Start frontend
:: ============================================
echo [2/2] Starting frontend...
echo   http://localhost:3000
echo.

start "AgentDevInsight Frontend" cmd /k "cd /d "%FRONTEND%" && npm run dev"

echo.
echo ========================================
echo  Services are starting...
echo.
echo    Frontend:  http://localhost:3000
echo    Backend:   http://localhost:8000
echo    API Docs:  http://localhost:8000/docs
echo.
echo  Close each service window to stop it
echo ========================================
echo.

:end
echo Press any key to close this window...
pause >nul
