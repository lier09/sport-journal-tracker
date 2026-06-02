@echo off
cd /d %~dp0\..
python -m src.main run-daily --days-back 7 --sources rss crossref pubmed --report
pause
