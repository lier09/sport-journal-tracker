@echo off
cd /d "%~dp0.."

if not exist "api.py" (
    echo Error: api.py not found.
    echo Current directory is:
    cd
    pause
    exit /b 1
)

if exist ".venv\Scripts\activate.bat" call ".venv\Scripts\activate.bat"

if not exist "frontend\node_modules" (
    echo Installing frontend dependencies...
    npm install --prefix frontend
    if errorlevel 1 goto failed
)

echo Building the React interface...
npm run build --prefix frontend
if errorlevel 1 goto failed

set APP_PRIVATE_MODE=1
python api.py
goto finished

:failed
echo Could not prepare the local web app. Confirm Python, Node.js, and npm are installed.

:finished

pause
