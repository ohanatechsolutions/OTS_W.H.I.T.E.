@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>&1
if %errorlevel%==0 (
  py -3 -m aegis_white.gui
) else (
  python -m aegis_white.gui
)
if errorlevel 1 (
  echo.
  echo Aegis White could not launch. Install Python 3.11+ with Tkinter.
  pause
)
endlocal
