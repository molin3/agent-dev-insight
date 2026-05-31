@echo off
setlocal

:: ============================================================
::  AgentDevInsight Setup
::  Double-click to run. Will NOT close on error.
:: ============================================================

:: Get project root: scripts\.. = project root
set "PROJECT=%~dp0.."
set "BACKEND=%PROJECT%\backend"
set "FRONTEND=%PROJECT%\frontend"

echo.
echo ========================================
echo  AgentDevInsight Setup
echo ========================================
echo.
echo  This script: %~f0
echo  Project dir: %PROJECT%
echo  Backend dir: %BACKEND%
echo  Frontend dir: %FRONTEND%
echo.

:: ============================================
:: Check: does backend folder exist?
:: ============================================
if not exist "%BACKEND%\requirements.txt" (
    echo [ERROR] Backend folder not found!
    echo.
    echo   Looking for: %BACKEND%\requirements.txt
    echo.
    echo   This usually means you need to enter the INNER folder.
    echo   If you extracted a ZIP, there might be two folders with
    echo   the same name nested inside each other.
    echo.
    echo   Make sure you run this script from:
    echo   agent-dev-insight-main\agent-dev-insight-main\scripts\setup.bat
    echo   (the INNER one, not the outer one)
    echo.
    goto :end
)

:: ============================================
:: Check: does frontend folder exist?
:: ============================================
if not exist "%FRONTEND%\package.json" (
    echo [ERROR] Frontend folder not found!
    echo   Looking for: %FRONTEND%\package.json
    goto :end
)

:: ============================================
:: Check: Python available?
:: ============================================
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH.
    echo.
    echo   Download: https://www.python.org/downloads/
    echo   IMPORTANT: Check "Add Python to PATH" during install.
    echo.
    goto :end
)

:: ============================================
:: Check: Node.js available?
:: ============================================
node --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Node.js is not installed or not in PATH.
    echo.
    echo   Download: https://nodejs.org/
    echo.
    goto :end
)

echo [0/3] Prerequisites OK
python --version
node --version
npm --version
echo.

:: ============================================
:: STEP 1: Backend
:: ============================================
echo [1/3] Setting up backend...
echo.

:: Delete incomplete venv if exists
if exist "%BACKEND%\venv" (
    if exist "%BACKEND%\venv\Scripts\python.exe" (
        echo   venv already exists, skipping creation.
        goto :do_pip
    )
    echo   Removing incomplete venv...
    rmdir /s /q "%BACKEND%\venv"
)

echo   Creating virtual environment (takes ~10 seconds)...
python -m venv "%BACKEND%\venv"
if not exist "%BACKEND%\venv\Scripts\python.exe" (
    echo [ERROR] Failed to create venv.
    echo   Try running manually: python -m venv venv
    goto :end
)
echo   venv created.

:do_pip
echo   Installing Python packages (takes 1-5 minutes)...
call "%BACKEND%\venv\Scripts\python.exe" -m pip install --disable-pip-version-check -r "%BACKEND%\requirements.txt"
if errorlevel 1 (
    echo [ERROR] pip install failed.
    goto :end
)
echo   Python packages installed.

:: Copy .env
if not exist "%BACKEND%\.env" (
    if exist "%PROJECT%\.env.example" (
        copy "%PROJECT%\.env.example" "%BACKEND%\.env" >nul
        echo   Created backend\.env from template.
    )
) else (
    echo   backend\.env already exists.
)

echo   Backend: DONE
echo.

:: ============================================
:: STEP 2: Frontend
:: ============================================
echo [2/3] Setting up frontend...
echo.

echo   Installing npm packages (takes 1-5 minutes)...
call npm install --prefix "%FRONTEND%"
if errorlevel 1 (
    echo [ERROR] npm install failed.
    goto :end
)
echo   npm packages installed.
echo   Frontend: DONE
echo.

:: ============================================
:: STEP 3: Verify
:: ============================================
echo [3/3] Verifying...
echo.

if exist "%BACKEND%\venv\Scripts\python.exe" (
    echo   [OK] Backend venv
) else (
    echo   [FAIL] Backend venv
)

if exist "%FRONTEND%\node_modules" (
    echo   [OK] Frontend node_modules
) else (
    echo   [FAIL] Frontend node_modules
)

if exist "%BACKEND%\.env" (
    echo   [OK] Backend .env
) else (
    echo   [WARN] Backend .env
)

echo.
echo ========================================
echo  Setup complete!
echo.
echo  Next: Run scripts\start.bat
echo ========================================
echo.

:end
echo.
echo Press any key to close this window...
pause >nul
