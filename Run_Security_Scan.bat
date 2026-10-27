@echo off
setlocal
cd /d "%~dp0"
set "TARGET=%~1"
if "%TARGET%"=="" set "TARGET=."
echo OTS W.H.I.T.E. - secrets/SAST only (SCA is explicitly skipped)
echo Scan target: %TARGET%
where py >nul 2>&1
if %errorlevel%==0 (
  py -3 -m ots_white "%TARGET%" --no-sca --history --format table
) else (
  python -m ots_white "%TARGET%" --no-sca --history --format table
)
set "CODE=%errorlevel%"
echo.
echo Exit code %CODE%: 0=clear/below threshold, 1=findings, 2=incomplete.
pause
exit /b %CODE%
