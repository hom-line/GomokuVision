@echo off
setlocal
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Run-Legacy-Modes-Windows.ps1" %*
set "EXITCODE=%ERRORLEVEL%"
echo.
if "%EXITCODE%"=="0" (echo V036_LEGACY_MODES_PASS) else (echo V036_LEGACY_MODES_FAIL)
echo Press any key to close this window.
pause >nul
exit /b %EXITCODE%
