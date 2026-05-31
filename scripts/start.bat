@echo off

echo.
echo ========================================
echo  AgentDevInsight Start
echo ========================================
echo.

set "PROJ=%~dp0.."
for %%A in ("%PROJ%") do set "PROJ=%%~fA"

set "BK=%PROJ%\backend"
set "FT=%PROJ%\frontend"

:: ============================================
:: Validate
:: ============================================
if exist "%BK%\venv\Scripts\python.exe" goto :venv_ok
echo [ERROR] Backend venv not found.
echo   Expected: %BK%\venv\Scripts\python.exe
echo   Solution: Run scripts\setup.bat first.
echo.
goto :end

:venv_ok
if exist "%FT%\node_modules" goto :all_ready
echo [ERROR] Frontend node_modules not found.
echo   Expected: %FT%\node_modules
echo   Solution: Run scripts\setup.bat first.
echo.
goto :end

:all_ready

:: ============================================
:: Start backend
:: ============================================
echo [1/2] Starting backend...
echo   http://localhost:8000
echo   http://localhost:8000/docs
echo.

start "AgentDevInsight Backend" cmd /k "cd /d "%BK%" && "%BK%\venv\Scripts\activate.bat" && uvicorn app.main:app --reload"

echo   Waiting for backend...
timeout /t 4 /nobreak >nul

:: ============================================
:: Start frontend
:: ============================================
echo [2/2] Starting frontend...
echo   http://localhost:3000
echo.

start "AgentDevInsight Frontend" cmd /k "cd /d "%FT%" && npm run dev"

echo.
echo ========================================
echo  Services starting...
echo.
echo    Frontend:  http://localhost:3000
echo    Backend:   http://localhost:8000
echo    API Docs:  http://localhost:8000/docs
echo.
echo  Close each window to stop
echo ========================================
echo.

:end
echo Press any key to close...
pause >nul
