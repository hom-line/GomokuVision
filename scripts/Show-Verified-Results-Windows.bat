@echo off
setlocal
set "VIEWER=%~dp0..\index.html"
if not exist "%VIEWER%" (echo Missing verified results viewer.&pause&exit /b 1)
start "" "%VIEWER%"
exit /b 0
