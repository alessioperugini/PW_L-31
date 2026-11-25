@echo off
cd /d "%~dp0"
if not exist .venv (
  echo Creazione ambiente virtuale...
  python -m venv .venv || (echo Python non trovato: installalo da python.org & pause & exit /b 1)
)
call .venv\Scripts\activate
pip install -q -r requirements.txt
echo.
echo Applicazione: http://localhost:8000    Documentazione API: http://localhost:8000/docs
echo Per fermare il server premi CTRL+C
python -m uvicorn app.main:app
pause
