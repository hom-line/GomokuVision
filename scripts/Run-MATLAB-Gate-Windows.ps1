param([string]$OutputDir='')
$ErrorActionPreference = 'Stop'
$root=(Resolve-Path (Join-Path $PSScriptRoot '..')).Path
if ([string]::IsNullOrWhiteSpace($OutputDir)) {
    $OutputDir=Join-Path $env:LOCALAPPDATA ('GomokuVision\Gates\matlab-'+(Get-Date -Format 'yyyyMMdd-HHmmss'))
}
New-Item -Force -ItemType Directory -Path $OutputDir | Out-Null
$log=Join-Path $OutputDir 'matlab-gate.log'
function Record([string]$message) { $message | Tee-Object -FilePath $log -Append }
$bin=$env:GOMOKUVISION_MATLAB_EXE
if ([string]::IsNullOrWhiteSpace($bin)) {
    $command=Get-Command matlab -ErrorAction SilentlyContinue
    if ($null -eq $command) {
        Record 'MATLAB_GATE_NOT_INSTALLED: Install licensed MATLAB + Image Processing Toolbox.'
        Record 'Set GOMOKUVISION_MATLAB_EXE to the full MATLAB matlab.exe path.'
        exit 2
    }
    $bin=$command.Source
}
if (-not (Test-Path $bin) -and -not (Get-Command $bin -ErrorAction SilentlyContinue)) {
    Record ('MATLAB_GATE_NOT_FOUND: '+$bin)
    exit 2
}
$py=Get-Command python -ErrorAction SilentlyContinue
if ($null -eq $py) { Record 'PYTHON_NOT_FOUND for oracle validation'; exit 2 }
$script=Join-Path $root 'matlab\modern'
$escapedScript=$script.Replace("'","''")
$configuration=Join-Path $OutputDir 'matlab-gate-config.json'
$escapedConfig=$configuration.Replace("'","''")
& $py.Source (Join-Path $root 'python\tools\make_matlab_gate_config.py') $OutputDir
if ($LASTEXITCODE -ne 0) { Record 'MATLAB_GATE_FAIL: config creation'; exit 1 }
$ErrorActionPreference = 'Continue'
& $bin -batch ("addpath('"+$escapedScript+"'); gomoku_selftest") 2>&1 | Tee-Object -FilePath $log -Append
$testExit=$LASTEXITCODE
if ($testExit -ne 0) { Record "MATLAB_GATE_FAIL: self-test exit=$testExit";exit 1 }
& $bin -batch ("addpath('"+$escapedScript+"'); gomoku_batch('"+$escapedConfig+"')") 2>&1 | Tee-Object -FilePath $log -Append
$runExit=$LASTEXITCODE
if ($runExit -ne 0) { Record "MATLAB_GATE_FAIL: native recognition exit=$runExit";exit 1 }
$ErrorActionPreference = 'Stop'
& $py.Source (Join-Path $root 'python\tools\verify_synthetic_expected.py') $OutputDir
if ($LASTEXITCODE -ne 0) { Record 'MATLAB_GATE_FAIL: 9-move oracle'; exit 1 }
Record 'MATLAB_GATE_PASS: native MATLAB detection + known nine-move oracle.'
exit 0
