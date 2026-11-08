@echo off
setlocal
cd /d "%~dp0.."
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Run-MATLAB-Gate-Windows.ps1"
set "R=%ERRORLEVEL%"
echo MATLAB gate exit code: %R%
pause
exit /b %R%
