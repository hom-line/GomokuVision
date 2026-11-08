@echo off
setlocal
cd /d "%~dp0"
set "SPEEDS=%*"
if "%SPEEDS%"=="" set "SPEEDS=1"
for /f %%G in ('powershell -NoProfile -Command "Get-Date -Format yyyyMMdd-HHmmss"') do set "RUNID=%%G"
set "OUTDIR=%LOCALAPPDATA%\GomokuVision\Benchmarks\multi-%RUNID%-%RANDOM%"
echo Selected playback speed labels: %SPEEDS%
echo Source video is analyzed anew for each speed/case, but playback speed does NOT accelerate recognition.
python python\tools\run_full_benchmark.py --input demo\full_game\full_game_961.mp4 --calibration demo\full_game\checkerboard_points.csv --black-template demo\full_game\black.png --white-template demo\full_game\white.png --output-dir "%OUTDIR%" --playback-speeds %SPEEDS%
set "RET=%ERRORLEVEL%"
echo.
echo Results: %OUTDIR%
echo BENCHMARK_EXIT=%RET%
pause
exit /b %RET%
