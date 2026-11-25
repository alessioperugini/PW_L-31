#!/bin/sh
cd "$(dirname "$0")"
[ -d .venv ] || python3 -m venv .venv
. .venv/bin/activate
pip install -q -r requirements.txt
echo "Applicazione: http://localhost:8000    Documentazione API: http://localhost:8000/docs"
python -m uvicorn app.main:app
