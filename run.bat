@echo off
CLS
title Installing Server Cloner...
set PATH=%PATH%;%~dp0
if not exist bot-env (
    echo 'bot-env' folder not found. Installing...
    python -m venv bot-env
    call .\bot-env\Scripts\activate.bat
    pip install -r requirements.txt

    cls

    echo Installed.
)

call .\bot-env\Scripts\activate.bat
title Discord Server Cloner
python "main.py"
pause