@echo off
setlocal EnableExtensions
set "LAUNCHER=%~dp0Launch-Desktop-Windows.ps1"
if not exist "%LAUNCHER%" (
  echo [ERROR] Missing launcher: "%LAUNCHER%"
  pause
  exit /b 2
)
where powershell.exe >nul 2>nul
if errorlevel 1 (
  echo [ERROR] Windows PowerShell not found.
  pause
  exit /b 3
)
echo ======================================================
echo  GomokuVision Advanced - Desktop Launcher (V0.2.3)
echo ======================================================
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%LAUNCHER%" %*
set "RC=%ERRORLEVEL%"
if not "%RC%"=="0" (
  echo.
  echo [ERROR] WPF launch failed. See the message above and saved diagnostic log.
  echo [INFO] A verified read-only results viewer may open in your browser.
  echo [INFO] No video analysis or benchmark was rerun.
  pause
)
exit /b %RC%
