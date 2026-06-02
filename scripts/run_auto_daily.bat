@echo off
cd /d "%~dp0.."

if not exist logs mkdir logs
call ".venv\Scripts\activate.bat"

echo ============================== >> logs\daily_run.log
echo Daily run started at %date% %time% >> logs\daily_run.log
python -m src.main run-daily --days-back 3 --sources crossref pubmed --report >> logs\daily_run.log 2>&1
echo Daily run finished at %date% %time% >> logs\daily_run.log
echo ============================== >> logs\daily_run.log
exit
