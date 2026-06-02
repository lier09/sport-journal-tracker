@echo off
cd /d "%~dp0.."

call ".venv\Scripts\activate.bat"

python -m src.main enrich-abstracts --limit 100 --batch-size 20

pause
