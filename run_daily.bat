@echo off
cd C:\projects\auto-trader-agent
call venv\Scripts\activate
python -m src.utils.report_merge
python -m src.utils.notion_report_sync
