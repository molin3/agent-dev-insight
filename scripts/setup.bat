@echo off
setlocal

echo ========================================
echo  AgentDevInsight Setup
echo ========================================
echo.

:: Resolve project root directory
set "PROJECT_DIR=%~dp0.."
echo  Project: %PROJECT_DIR%
echo.

:: Check Python (try python3 first, then python)
python --version >nul 2>&1
if errorlevel 1 (
    python3 --version >nul 2>&1
    if errorlevel 1 (
        echo [ERROR] Python not found. Please install Python 3.11+
        echo Download: https://www.python.org/downloads/
        echo Make sure to check "Add Python to PATH" during installation.
        pause
        exit /b 1
    ) else (
        set "PYTHON=python3"
    )
) else (
    set "PYTHON=python"
)

:: Check Node.js
node --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Node.js not found. Please install Node.js 18+
    echo Download: https://nodejs.org/
    pause
    exit /b 1
)

echo [1/4] Checking versions...
%PYTHON% --version
node --version
npm --version
echo.

:: Backend setup
echo [2/4] Setting up backend...
cd /d "%PROJECT_DIR%\backend"
if errorlevel 1 (
    echo [ERROR] Cannot find backend directory at: %PROJECT_DIR%\backend
    pause
    exit /b 1
)

if not exist "venv" (
    echo   Creating virtual environment (this may take a moment)...
    %PYTHON% -m venv venv
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment.
        echo Try running: %PYTHON% -m venv venv
        pause
        exit /b 1
    )
    echo   Virtual environment created.
) else (
    echo   Virtual environment already exists, skipping creation.
)

:: Verify venv was created
if not exist "venv\Scripts\python.exe" (
    echo [ERROR] Virtual environment creation appeared to succeed but
    echo         venv\Scripts\python.exe not found.
    echo         Try deleting the venv folder and running setup again.
    pause
    exit /b 1
)

echo   Installing backend dependencies (this may take a few minutes)...
call venv\Scripts\activate.bat
pip install -r requirements.txt
if errorlevel 1 (
    echo [ERROR] Failed to install backend dependencies.
    pause
    exit /b 1
)
echo   Backend dependencies installed.

:: Copy env template
if not exist ".env" (
    if exist "%PROJECT_DIR%\.env.example" (
        echo   Copying .env template...
        copy "%PROJECT_DIR%\.env.example" ".env" >nul
        echo   NOTE: Edit backend\.env to configure your settings if needed.
    )
) else (
    echo   .env already exists, skipping.
)

echo   Backend setup complete.
echo.

:: Frontend setup
echo [3/4] Setting up frontend...
cd /d "%PROJECT_DIR%\frontend"
if errorlevel 1 (
    echo [ERROR] Cannot find frontend directory at: %PROJECT_DIR%\frontend
    pause
    exit /b 1
)

echo   Installing frontend dependencies (this may take a few minutes)...
call npm install
if errorlevel 1 (
    echo [ERROR] Failed to install frontend dependencies.
    pause
    exit /b 1
)
echo   Frontend dependencies installed.
echo.

:: Final verification
echo [4/4] Verifying setup...
if exist "%PROJECT_DIR%\backend\venv\Scripts\python.exe" (
    echo   [OK] Backend virtual environment
) else (
    echo   [FAIL] Backend virtual environment
)
if exist "%PROJECT_DIR%\frontend\node_modules" (
    echo   [OK] Frontend node_modules
) else (
    echo   [FAIL] Frontend node_modules
)
if exist "%PROJECT_DIR%\backend\.env" (
    echo   [OK] Backend .env config
) else (
    echo   [WARN] Backend .env not found (will use defaults)
)
echo.

echo ========================================
echo  Setup complete!
echo.
echo  Next step: Run scripts\start.bat
echo ========================================
echo.

pause
