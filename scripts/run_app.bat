@echo off
cd /d "%~dp0.."

if not exist "app.py" (
    echo Error: app.py not found.
    echo Current directory is:
    cd
    pause
    exit /b 1
)

call ".venv\Scripts\activate.bat"

python -m streamlit run app.py

pause
