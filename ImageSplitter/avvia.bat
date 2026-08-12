@echo off
cd /d "%~dp0"
if not exist ".venv" (
    echo Creazione ambiente virtuale in corso...
    python -m venv .venv
)
call .venv\Scripts\activate.bat
echo Installazione dipendenze in corso...
pip install -r requirements.txt
echo Avvio del programma...
python app.py
pause
