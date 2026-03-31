@echo off
set "VENV_PYTHON=venv\Scripts\python.exe"
echo Starting SAZA AI Employee System...

echo [1/5] Launching Inbox Watcher...
start "SAZA Inbox Watcher" cmd /k "%VENV_PYTHON% scripts/inbox_watcher.py"

echo [2/5] Launching Gmail Watcher...
echo NOTE: First run will open a browser for OAuth authentication.
start "SAZA Gmail Watcher" cmd /k "%VENV_PYTHON% scripts/gmail_watcher.py"

echo [2.5/5] Launching WhatsApp Watcher...
echo NOTE: First run requires scanning QR code.
start "SAZA WhatsApp Watcher" cmd /k "%VENV_PYTHON% scripts/whatsapp_watcher.py"

echo [2.7/5] Launching Approved Watcher (AI Processor)...
start "SAZA Approved Watcher" cmd /k "%VENV_PYTHON% scripts/approved_watcher.py"

echo [3/5] Launching LinkedIn Watcher...
echo NOTE: Requires linkedin_cookies.json for authentication.
start "SAZA LinkedIn Watcher" cmd /k "%VENV_PYTHON% scripts/linkedin_watcher.py"

echo [4/5] Launching LinkedIn Poster...
start "SAZA LinkedIn Poster" cmd /k "%VENV_PYTHON% scripts/linkedin_poster.py"

echo [5/5] Launching Dashboard...
start "SAZA Dashboard" cmd /k "%VENV_PYTHON% dashboard/dashboard.py"

echo.
echo System is Live!
echo Dashboard: http://localhost:5000
echo Watchers and Poster are running in separate windows.
echo.
pause

