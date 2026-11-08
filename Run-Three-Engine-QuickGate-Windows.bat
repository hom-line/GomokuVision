@echo off
setlocal
pushd "%~dp0"
echo [1/2] Python + C# synthetic video, cross-engine parity, WPF Release build
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\Quick-Engine-Gate-Windows.ps1"
if errorlevel 1 goto failed
echo [2/2] Native MATLAB 9-move synthetic acceptance (requires licensed MATLAB)
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\Run-MATLAB-Gate-Windows.ps1"
if errorlevel 1 goto failed
echo THREE_ENGINE_QUICK_GATE_PASS
popd
pause
exit /b 0
:failed
echo THREE_ENGINE_QUICK_GATE_FAIL
popd
pause
exit /b 1
