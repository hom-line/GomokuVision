param([string]$OutputDir = '')
$ErrorActionPreference = 'Stop'
$root = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
if (-not $OutputDir) {
    $OutputDir = Join-Path $env:LOCALAPPDATA ('GomokuVision\Gates\matlab-full961-' + (Get-Date -Format 'yyyyMMdd-HHmmss'))
}
New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null
$log = Join-Path $OutputDir 'matlab-961.log'
function Record([string]$message) { $message | Tee-Object -FilePath $log -Append }
$matlab = $env:GOMOKUVISION_MATLAB_EXE
if (-not $matlab) {
    $cmd = Get-Command matlab -ErrorAction SilentlyContinue
    if ($cmd) { $matlab=$cmd.Source }
}
if (-not $matlab) {
    Record 'MATLAB_NOT_FOUND: configure licensed MATLAB and Image Processing Toolbox.'
    exit 2
}
$source = Join-Path $root 'demo\full_game'
$inputFile = Join-Path $source 'full_game_961.mp4'
$configFile = Join-Path $OutputDir 'matlab-config.json'
$config = @{
    input=$inputFile
    calibration=(Join-Path $source 'checkerboard_points.csv')
    black_template=(Join-Path $source 'black.png')
    white_template=(Join-Path $source 'white.png')
    output_dir=$OutputDir
    sample_every=6
    full_scan_every=4
    confirmations=2
    local_radius=6
    scale=0.5
    black_threshold=0.65
    white_threshold=0.75
    progress_file=(Join-Path $OutputDir 'matlab-progress.json')
    cancel_file=(Join-Path $OutputDir '.cancel-request')
} | ConvertTo-Json -Depth 5
[System.IO.File]::WriteAllText($configFile,$config,(New-Object System.Text.UTF8Encoding($false)))
$work=Join-Path $root 'matlab\modern'
$escapedWork=$work.Replace("'","''")
$escapedConfig=$configFile.Replace("'","''")
Record 'MATLAB 961 GATE: native MATLAB, self-authored complete game; NOT historical third-party footage.'
$clock=[System.Diagnostics.Stopwatch]::StartNew()
# Preserve MATLAB native diagnostics; stderr from native apps is not by itself a fatal PS 5.1 exception.
$ErrorActionPreference='Continue'
& $matlab -batch ("addpath('"+$escapedWork+"'); gomoku_selftest; gomoku_batch('"+$escapedConfig+"')") 2>&1 | Tee-Object -FilePath $log -Append
$code=$LASTEXITCODE
$clock.Stop()
$ErrorActionPreference='Stop'
if ($code -ne 0) { Record ("MATLAB_961_GATE_FAIL: MATLAB exit="+$code); exit 1 }
$python=Get-Command python -ErrorAction SilentlyContinue
if (-not $python) { Record 'MATLAB_961_GATE_FAIL: python needed for oracle comparison'; exit 2 }
& $python.Source (Join-Path $root 'python\tools\verify_full_game_41.py') $OutputDir 2>&1 | Tee-Object -FilePath $log -Append
if ($LASTEXITCODE -ne 0) { Record 'MATLAB_961_GATE_FAIL: 41-move oracle mismatch'; exit 1 }
Record ('MATLAB_961_GATE_PASS: elapsed wall_seconds=' + [Math]::Round($clock.Elapsed.TotalSeconds,2))
Record ('Output: '+$OutputDir)
exit 0
