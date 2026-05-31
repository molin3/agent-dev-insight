@echo off

echo.
echo ========================================
echo  AgentDevInsight Setup
echo ========================================
echo.

:: Resolve project root
set "PROJ=%~dp0.."
for %%A in ("%PROJ%") do set "PROJ=%%~fA"

set "BK=%PROJ%\backend"
set "FT=%PROJ%\frontend"

echo  Project: %PROJ%
echo  Backend: %BK%
echo  Frontend: %FT%
echo.

:: ============================================
:: Check backend folder
:: ============================================
if exist "%BK%\requirements.txt" goto :backend_ok
echo [ERROR] Backend folder not found!
echo   Looking for: %BK%\requirements.txt
echo.
echo   If using GitHub ZIP, there might be two folders
echo   with the same name nested inside each other.
echo   Make sure you are in the INNER folder.
echo.
goto :end

:backend_ok
echo [OK] Backend folder found

:: ============================================
:: Check frontend folder
:: ============================================
if exist "%FT%\package.json" goto :frontend_ok
echo [ERROR] Frontend folder not found!
echo   Looking for: %FT%\package.json
echo.
goto :end

:frontend_ok
echo [OK] Frontend folder found

:: ============================================
:: Check Python
:: ============================================
python --version 2>nul
if not errorlevel 1 goto :python_ok
echo.
echo [ERROR] Python not found in PATH.
echo   Download: https://www.python.org/downloads/
echo   Check "Add Python to PATH" during install.
echo.
goto :end

:python_ok
echo [OK] Python found

:: ============================================
:: Check Node
:: ============================================
node --version 2>nul
if not errorlevel 1 goto :node_ok
echo.
echo [ERROR] Node.js not found in PATH.
echo   Download: https://nodejs.org/
echo.
goto :end

:node_ok
echo [OK] Node.js found
echo.

:: ============================================
:: STEP 1: Backend
:: ============================================
echo [1/3] Backend setup
echo.

:: Remove incomplete venv
if not exist "%BK%\venv" goto :create_venv
if exist "%BK%\venv\Scripts\python.exe" goto :venv_ready
echo   Removing incomplete venv...
rmdir /s /q "%BK%\venv"

:create_venv
echo   Creating virtual environment...
python -m venv "%BK%\venv"
if not exist "%BK%\venv\Scripts\python.exe" (
    echo [ERROR] venv creation failed.
    goto :end
)
echo   venv created.

:venv_ready
echo   Installing Python packages (1-5 min)...
"%BK%\venv\Scripts\python.exe" -m pip install --disable-pip-version-check -q -r "%BK%\requirements.txt"
if errorlevel 1 (
    echo [ERROR] pip install failed.
    goto :end
)
echo   Python packages installed.

:: Copy .env
if exist "%BK%\.env" goto :env_done
if not exist "%PROJ%\.env.example" goto :env_done
copy "%PROJ%\.env.example" "%BK%\.env" >nul
echo   Created backend\.env from template.
:env_done
echo   Backend: DONE
echo.

:: ============================================
:: STEP 2: Frontend
:: ============================================
echo [2/3] Frontend setup
echo.

echo   Installing npm packages (1-5 min)...
cd /d "%FT%"
call npm install
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
echo [3/3] Verification
echo.

if exist "%BK%\venv\Scripts\python.exe" echo   [OK] Backend venv
if not exist "%BK%\venv\Scripts\python.exe" echo   [FAIL] Backend venv

if exist "%FT%\node_modules" echo   [OK] Frontend node_modules
if not exist "%FT%\node_modules" echo   [FAIL] Frontend node_modules

if exist "%BK%\.env" echo   [OK] Backend .env
if not exist "%BK%\.env" echo   [WARN] Backend .env

echo.
echo ========================================
echo  Setup complete!
echo  Now run: scripts\start.bat
echo ========================================
echo.

:end
echo Press any key to close...
pause >nul
