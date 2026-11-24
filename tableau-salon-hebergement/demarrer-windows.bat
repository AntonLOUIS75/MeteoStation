@echo off
cd /d "%~dp0"
where py >nul 2>nul
if errorlevel 1 (
  set "PYTHON_CMD=python"
) else (
  set "PYTHON_CMD=py"
)
if not exist ".venv\Scripts\python.exe" %PYTHON_CMD% -m venv .venv
if errorlevel 1 goto error
.venv\Scripts\python.exe -m pip install -r requirements.txt
if errorlevel 1 goto error
set "HOST=127.0.0.1"
set "PORT=8000"
echo Ouvre http://localhost:8000 dans ton navigateur.
.venv\Scripts\python.exe server.py
pause
exit /b
:error
echo Installation impossible. Verifie Python et la connexion Internet.
pause
