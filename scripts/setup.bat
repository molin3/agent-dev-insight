@echo off
setlocal EnableDelayedExpansion

:: ============================================================
::  AgentDevInsight Setup Script
::  Usage: Double-click scripts\setup.bat
:: ============================================================

:: Resolve absolute paths (never change these)
set "SCRIPT_DIR=%~dp0"
set "PROJECT_DIR=%SCRIPT_DIR%.."
set "BACKEND_DIR=%PROJECT_DIR%\backend"
set "FRONTEND_DIR=%PROJECT_DIR%\frontend"

echo ========================================
echo  AgentDevInsight Setup
echo ========================================
echo  Project: %PROJECT_DIR%
echo.

:: ---- Step 0: Check prerequisites ----

:: Find Python executable
set "PYTHON_CMD="
python --version >nul 2>&1
if not errorlevel 1 (
    set "PYTHON_CMD=python"
    goto :python_found
)
python3 --version >nul 2>&1
if not errorlevel 1 (
    set "PYTHON_CMD=python3"
    goto :python_found
)
py -3 --version >nul 2>&1
if not errorlevel 1 (
    set "PYTHON_CMD=py -3"
    goto :python_found
)

echo [ERROR] Python not found!
echo.
echo Please install Python 3.11+ from: https://www.python.org/downloads/
echo IMPORTANT: Check "Add Python to PATH" during installation.
echo.
pause
exit /b 1

:python_found

node --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Node.js not found!
    echo.
    echo Please install Node.js 18+ from: https://nodejs.org/
    echo.
    pause
    exit /b 1
)

echo [0/3] Prerequisites OK
%PYTHON_CMD% --version
node --version
npm --version
echo.

:: ---- Step 1: Backend ----
echo [1/3] Setting up backend...

:: Verify backend directory exists
if not exist "%BACKEND_DIR%\requirements.txt" (
    echo [ERROR] Backend directory not found or incomplete:
    echo   Expected: %BACKEND_DIR%\requirements.txt
    echo.
    pause
    exit /b 1
)

:: Handle incomplete venv: delete and recreate
if exist "%BACKEND_DIR%\venv" (
    if exist "%BACKEND_DIR%\venv\Scripts\python.exe" (
        echo   Virtual environment exists, skipping creation.
        goto :venv_ready
    ) else (
        echo   Found incomplete venv, removing and recreating...
        rmdir /s /q "%BACKEND_DIR%\venv"
    )
)

echo   Creating virtual environment...
pushd "%BACKEND_DIR%"
%PYTHON_CMD% -m venv venv
set "VENV_RESULT=%errorlevel%"
popd

if not %VENV_RESULT%==0 (
    echo [ERROR] Failed to create virtual environment.
    echo Try running manually: %PYTHON_CMD% -m venv venv
    pause
    exit /b 1
)

:: Verify creation succeeded
if not exist "%BACKEND_DIR%\venv\Scripts\python.exe" (
    echo [ERROR] venv creation reported success but python.exe not found.
    echo Please delete %BACKEND_DIR%\venv and try again.
    pause
    exit /b 1
)
echo   Virtual environment created.

:venv_ready

:: Install Python dependencies (use absolute paths, never rely on cd)
echo   Installing Python dependencies...
call "%BACKEND_DIR%\venv\Scripts\activate.bat"
pip install -r "%BACKEND_DIR%\requirements.txt"
if errorlevel 1 (
    echo [ERROR] pip install failed. Check your internet connection.
    pause
    exit /b 1
)
echo   Python dependencies installed.

:: Copy .env template
if not exist "%BACKEND_DIR%\.env" (
    if exist "%PROJECT_DIR%\.env.example" (
        copy "%PROJECT_DIR%\.env.example" "%BACKEND_DIR%\.env" >nul
        echo   Created backend\.env from template.
    )
) else (
    echo   backend\.env already exists.
)
echo   Backend setup complete.
echo.

:: ---- Step 2: Frontend ----
echo [2/3] Setting up frontend...

if not exist "%FRONTEND_DIR%\package.json" (
    echo [ERROR] Frontend directory not found:
    echo   Expected: %FRONTEND_DIR%\package.json
    echo.
    pause
    exit /b 1
)

pushd "%FRONTEND_DIR%"
call npm install
set "NPM_RESULT=%errorlevel%"
popd

if not %NPM_RESULT%==0 (
    echo [ERROR] npm install failed. Check your internet connection.
    pause
    exit /b 1
)
echo   Frontend dependencies installed.
echo.

:: ---- Step 3: Verify ----
echo [3/3] Verifying installation...

set "ALL_OK=1"

if exist "%BACKEND_DIR%\venv\Scripts\python.exe" (
    echo   [OK] Backend virtual environment
) else (
    echo   [FAIL] Backend virtual environment
    set "ALL_OK=0"
)

if exist "%FRONTEND_DIR%\node_modules" (
    echo   [OK] Frontend node_modules
) else (
    echo   [FAIL] Frontend node_modules
    set "ALL_OK=0"
)

if exist "%BACKEND_DIR%\.env" (
    echo   [OK] Backend .env
) else (
    echo   [WARN] Backend .env missing (will use defaults)
)

echo.

if "%ALL_OK%"=="0" (
    echo [ERROR] Setup incomplete! Please check errors above.
    pause
    exit /b 1
)

echo ========================================
echo  Setup complete!
echo.
echo  Next: Run scripts\start.bat
echo ========================================
echo.

pause
