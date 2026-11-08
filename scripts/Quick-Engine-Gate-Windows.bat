@echo off
setlocal
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Quick-Engine-Gate-Windows.ps1" %*
set "EXITCODE=%ERRORLEVEL%"
echo.
if "%EXITCODE%"=="0" (echo QUICK_ENGINE_GATE_PASS) else (echo QUICK_ENGINE_GATE_FAIL - see %%LOCALAPPDATA%%\GomokuVision\Gates)
echo Press any key to close this window.
pause >nul
exit /b %EXITCODE%
