@echo off
cd /d "%~dp0.."

if not exist logs mkdir logs
call ".venv\Scripts\activate.bat"

echo ============================== >> logs\weekly_run.log
echo Weekly report started at %date% %time% >> logs\weekly_run.log
python -m src.main make-weekly-report >> logs\weekly_run.log 2>&1
echo Weekly report finished at %date% %time% >> logs\weekly_run.log
echo ============================== >> logs\weekly_run.log
exit
