@echo off
cd /d "%~dp0\.."
call ".venv\Scripts\activate.bat"
python -m src.main run-daily --days-back 7 --sources publisher --report
pause
