@echo off
setlocal
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\Run-MATLAB-961-Gate-Windows.ps1"
set "result=%ERRORLEVEL%"
echo.
if "%result%"=="0" (
 echo MATLAB_961_GATE_PASS
) else (
 echo MATLAB_961_GATE_FAIL code=%result%
)
echo Press any key to close...
pause >nul
exit /b %result%
