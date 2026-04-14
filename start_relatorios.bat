@echo off
TITLE HEMN Reports System
echo Iniciando Sistema de Relatorios...
cd /d "%~dp0"
python -m streamlit run app.py
pause
