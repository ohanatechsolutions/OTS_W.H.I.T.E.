@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>&1
if %errorlevel%==0 (
  py -3 -m ots_white.gui
) else (
  python -m ots_white.gui
)
if errorlevel 1 (
  echo.
  echo OTS W.H.I.T.E. could not launch. Install Python 3.11+ with Tkinter.
  pause
)
endlocal
