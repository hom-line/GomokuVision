@echo off
setlocal
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Run-All-Local-Windows.ps1" %*
exit /b %ERRORLEVEL%
