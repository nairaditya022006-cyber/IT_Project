@echo off
echo Setting up TaskFlow Virtual Environment...
if not exist venv (
    python -m venv venv
)
call venv\Scripts\activate.bat
echo Installing dependencies...
pip install -r requirements.txt
echo Starting TaskFlow...
python app.py
pause
