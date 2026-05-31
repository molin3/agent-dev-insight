@echo off
setlocal

:: ============================================================
::  AgentDevInsight Start
::  Run this AFTER setup.bat has completed successfully
:: ============================================================

set "SELF=%~dp0"
set "SELF=%SELF:~0,-1%"
for %%I in ("%SELF%") do set "PROJECT=%%~dpI"
set "PROJECT=%PROJECT:~0,-1%"

set "BACKEND=%PROJECT%\backend"
set "FRONTEND=%PROJECT%\frontend"

echo.
echo ========================================
echo  AgentDevInsight Start
echo ========================================
echo.

:: ---- Validate ----
set "READY=1"

if not exist "%BACKEND%\venv\Scripts\python.exe" (
    echo [ERROR] Backend venv not found.
    echo   Expected: %BACKEND%\venv\Scripts\python.exe
    echo.
    echo   Solution: Run scripts\setup.bat first.
    echo.
    set "READY=0"
)

if not exist "%FRONTEND%\node_modules" (
    echo [ERROR] Frontend node_modules not found.
    echo   Expected: %FRONTEND%\node_modules
    echo.
    echo   Solution: Run scripts\setup.bat first.
    echo.
    set "READY=0"
)

if "%READY%"=="0" (
    pause
    exit /b 1
)

:: ---- Start backend ----
echo [1/2] Starting backend...
echo        http://localhost:8000
echo        http://localhost:8000/docs
echo.

start "AgentDevInsight Backend" cmd /k "cd /d "%BACKEND%" && call venv\Scripts\activate.bat && uvicorn app.main:app --reload"

echo   Waiting for backend...
timeout /t 4 /nobreak >nul

:: ---- Start frontend ----
echo [2/2] Starting frontend...
echo        http://localhost:3000
echo.

start "AgentDevInsight Frontend" cmd /k "cd /d "%FRONTEND%" && npm run dev"

echo.
echo ========================================
echo  Services starting...
echo.
echo    Frontend:  http://localhost:3000
echo    Backend:   http://localhost:8000
echo    API Docs:  http://localhost:8000/docs
echo.
echo  Close the window to stop each service
echo ========================================
echo.

pause
