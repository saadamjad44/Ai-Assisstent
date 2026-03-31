@echo off
:: SAZA AI Employee - Windows Task Scheduler Setup
:: This script registers scheduled tasks for daily operations

echo ================================================
echo SAZA AI Employee - Task Scheduler Setup
echo ================================================
echo.

set "PYTHON_PATH=d:\practice\AI_Employee\venv\Scripts\python.exe"
set "SCRIPTS_PATH=d:\practice\AI_Employee\scripts"

:: 1. Daily Briefing at 8:00 AM
echo [1/3] Creating Daily Briefing task (8:00 AM)...
schtasks /create /tn "SAZA_Daily_Briefing" /tr "\"%PYTHON_PATH%\" -c \"from orchestrator import Orchestrator; o = Orchestrator('d:/practice/AI_Employee/AI-Employee-Vault'); o.generate_daily_briefing()\"" /sc daily /st 08:00 /f

:: 2. Health Check every 6 hours
echo [2/3] Creating Health Check task (every 6 hours)...
schtasks /create /tn "SAZA_Health_Check" /tr "\"%PYTHON_PATH%\" -c \"print('SAZA Health Check OK')\"" /sc daily /st 06:00 /ri 360 /du 24:00 /f

:: 3. Optional: Start watchers on system login
echo [3/3] Creating Startup task (on login)...
schtasks /create /tn "SAZA_Startup" /tr "d:\practice\AI_Employee\start_saza.bat" /sc onlogon /f

echo.
echo ================================================
echo Setup Complete! Tasks registered:
echo   - SAZA_Daily_Briefing (8:00 AM daily)
echo   - SAZA_Health_Check (every 6 hours)
echo   - SAZA_Startup (on login)
echo.
echo To view tasks: taskschd.msc
echo To delete tasks: schtasks /delete /tn "SAZA_*" /f
echo ================================================
pause
