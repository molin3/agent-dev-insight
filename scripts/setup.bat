@echo off
setlocal

echo ========================================
echo  AgentDevInsight Setup
echo ========================================
echo.

:: Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found. Please install Python 3.11+
    echo Download: https://www.python.org/downloads/
    pause
    exit /b 1
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
python --version
node --version
npm --version
echo.

:: Backend setup
echo [2/4] Setting up backend...
cd /d "%~dp0..\backend"

if not exist "venv" (
    echo   Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment
        pause
        exit /b 1
    )
) else (
    echo   Virtual environment already exists, skipping
)

echo   Installing backend dependencies...
call venv\Scripts\activate.bat
pip install -r requirements.txt
if errorlevel 1 (
    echo [ERROR] Failed to install backend dependencies
    pause
    exit /b 1
)

:: Copy env template
if not exist ".env" (
    if exist "..\.env.example" (
        echo   Copying .env template...
        copy "..\.env.example" ".env" >nul
        echo   Please edit backend\.env to configure your settings
    )
) else (
    echo   .env already exists, skipping
)

echo   Backend setup complete
echo.

:: Frontend setup
echo [3/4] Setting up frontend...
cd /d "%~dp0..\frontend"
echo   Installing frontend dependencies...
call npm install
if errorlevel 1 (
    echo [ERROR] Failed to install frontend dependencies
    pause
    exit /b 1
)
echo   Frontend setup complete
echo.

echo [4/4] Setup complete!
echo.
echo ========================================
echo  Next steps:
echo  1. Edit backend\.env with your config
echo  2. Run scripts\start.bat to launch
echo ========================================
echo.

pause
