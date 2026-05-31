@echo off
setlocal EnableDelayedExpansion

:: ============================================================
::  AgentDevInsight Setup
::  Right-click this file -> Run as administrator (if needed)
:: ============================================================

:: Get this script's directory, then project root (parent)
set "SELF=%~dp0"
:: Remove trailing backslash from SELF
set "SELF=%SELF:~0,-1%"
:: Get parent directory
for %%I in ("%SELF%") do set "PROJECT=%%~dpI"
:: Remove trailing backslash
set "PROJECT=%PROJECT:~0,-1%"

set "BACKEND=%PROJECT%\backend"
set "FRONTEND=%PROJECT%\frontend"

echo.
echo ========================================
echo  AgentDevInsight Setup
echo ========================================
echo.
echo  Script dir:  %SELF%
echo  Project root: %PROJECT%
echo  Backend:      %BACKEND%
echo  Frontend:     %FRONTEND%
echo.

:: ---- Check Python ----
set "PYCMD="
where python >nul 2>&1 && set "PYCMD=python"
if not defined PYCMD where python3 >nul 2>&1 && set "PYCMD=python3"
if not defined PYCMD where py >nul 2>&1 && set "PYCMD=py -3"

if not defined PYCMD (
    echo [ERROR] Python not found. Install Python 3.11+ and add to PATH.
    echo https://www.python.org/downloads/
    pause
    exit /b 1
)

:: ---- Check Node ----
where node >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Node.js not found. Install Node.js 18+.
    echo https://nodejs.org/
    pause
    exit /b 1
)

echo [STEP 0/3] Prerequisites
%PYCMD% --version
node --version
npm --version
echo.

:: ============================================================
::  STEP 1: Backend
:: ============================================================
echo [STEP 1/3] Backend setup
echo.

:: Verify backend dir
if not exist "%BACKEND%\requirements.txt" (
    echo [ERROR] Cannot find: %BACKEND%\requirements.txt
    echo Make sure you are in the correct project directory.
    pause
    exit /b 1
)

:: Remove incomplete venv if exists
if exist "%BACKEND%\venv" (
    if exist "%BACKEND%\venv\Scripts\python.exe" (
        echo   venv already exists - skipping creation.
        goto :install_deps
    ) else (
        echo   Found incomplete venv - removing...
        rmdir /s /q "%BACKEND%\venv"
    )
)

:: Create venv
echo   Creating virtual environment...
%PYCMD% -m venv "%BACKEND%\venv"
if not exist "%BACKEND%\venv\Scripts\python.exe" (
    echo [ERROR] venv creation failed.
    echo Try: %PYCMD% -m venv "%BACKEND%\venv"
    pause
    exit /b 1
)
echo   venv created successfully.

:install_deps
echo   Installing Python packages (may take a few minutes)...
call "%BACKEND%\venv\Scripts\activate.bat"
pip install --disable-pip-version-check -r "%BACKEND%\requirements.txt"
if errorlevel 1 (
    echo [ERROR] pip install failed. Check internet connection.
    pause
    exit /b 1
)
echo   Python packages installed.

:: Copy .env if needed
if not exist "%BACKEND%\.env" (
    if exist "%PROJECT%\.env.example" (
        copy "%PROJECT%\.env.example" "%BACKEND%\.env" >nul
        echo   Created backend\.env from template.
    )
) else (
    echo   backend\.env already exists.
)

echo   Backend: OK
echo.

:: ============================================================
::  STEP 2: Frontend
:: ============================================================
echo [STEP 2/3] Frontend setup
echo.

if not exist "%FRONTEND%\package.json" (
    echo [ERROR] Cannot find: %FRONTEND%\package.json
    pause
    exit /b 1
)

echo   Installing npm packages (may take a few minutes)...
cd /d "%FRONTEND%"
call npm install
if errorlevel 1 (
    echo [ERROR] npm install failed. Check internet connection.
    pause
    exit /b 1
)
echo   npm packages installed.
echo   Frontend: OK
echo.

:: ============================================================
::  STEP 3: Verify
:: ============================================================
echo [STEP 3/3] Verification
echo.

set "OK=1"

if exist "%BACKEND%\venv\Scripts\python.exe" (
    echo   [OK] Backend venv
) else (
    echo   [FAIL] Backend venv
    set "OK=0"
)

if exist "%FRONTEND%\node_modules\.package-lock.json" (
    echo   [OK] Frontend node_modules
) else (
    echo   [FAIL] Frontend node_modules
    set "OK=0"
)

if exist "%BACKEND%\.env" (
    echo   [OK] backend\.env
) else (
    echo   [WARN] backend\.env missing
)

echo.

if "!OK!"=="0" (
    echo [FAILED] Setup incomplete. Check errors above.
    pause
    exit /b 1
)

echo ========================================
echo  Setup complete!
echo.
echo  Now run: scripts\start.bat
echo ========================================
echo.

pause
