@echo off
cd /d "%~dp0"
.venv\Scripts\streamlit.exe run job_tracker/streamlit_app/main.py
pause
