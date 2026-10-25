@echo off
cd /d "%~dp0\.."
if not exist ".venv\Scripts\python.exe" (
  echo Run scripts\setup_and_test.cmd first.
  pause
  exit /b 1
)
.venv\Scripts\python.exe scripts\install_test.py %*
pause
