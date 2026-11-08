param(
    [switch]$SkipWpfBuild
)
$ErrorActionPreference = 'Stop'
$root = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$logs = Join-Path $env:LOCALAPPDATA 'GomokuVision\Gates'
New-Item -ItemType Directory -Force -Path $logs | Out-Null
$stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$log = Join-Path $logs ("quick-gate-$stamp.log")
$report = Join-Path $logs ("quick-gate-$stamp.json")
$latest = Join-Path $logs 'quick-gate-latest.json'
$output = Join-Path $logs ("synthetic-$stamp")
New-Item -ItemType Directory -Force -Path $output | Out-Null
$checks = New-Object 'System.Collections.Generic.List[object]'
$failed = $null
$started = Get-Date
$exitStatus = 1
$wpfAttempted = $false
$env:PYTHONPATH = Join-Path $root 'python'

function LogText([string]$Message) {
    Write-Host $Message
    Add-Content -LiteralPath $log -Value $Message -Encoding UTF8
}
function Gate([string]$Name, [string]$Exe, [string[]]$ArgsList) {
    LogText ('>>> ' + $Name)
    $start = Get-Date
    # Native stderr can be categorized as a PowerShell error in PS 5.1;
    # the process exit code is the authoritative gate result.
    $previous = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    try {
        & $Exe @ArgsList 2>&1 | Out-File -FilePath $log -Append -Encoding UTF8
        $code = $LASTEXITCODE
    }
    finally { $ErrorActionPreference = $previous }
    $elapsed = [Math]::Round(((Get-Date)-$start).TotalSeconds,2)
    if ($null -eq $code) { $code = 1 }
    $checks.Add([pscustomobject]@{ name=$Name; exit_code=[int]$code; elapsed_seconds=$elapsed })
    if ($code -ne 0) {
        LogText ('GATE_FAIL: ' + $Name + ' exit=' + $code)
        Get-Content -LiteralPath $log -Tail 28 | ForEach-Object { Write-Host $_ }
        throw ('FAILED_STEP: ' + $Name + ' exit=' + $code)
    }
    LogText ('GATE_PASS: ' + $Name + ' (' + $elapsed + ' s)')
}

try {
    LogText 'GomokuVision V0.3.3 QUICK ENGINE GATE — synthetic demo only'
    LogText ('Project: ' + $root)
    LogText ('Evidence: ' + $report)
    LogText 'SAFE: This gate NEVER opens or processes the historical third-party 961-frame video.'
    LogText 'MATLAB native engine has a separate explicit gate (Run-MATLAB-Gate-Windows.bat); not included in Python/C# PASS.'
    foreach ($relative in @('demo\demo.mp4','demo\black.png','demo\white.png','demo\checkerboard_points.csv')) {
        if (-not (Test-Path -LiteralPath (Join-Path $root $relative))) {
            throw ('MISSING_SYNTHETIC_INPUT: ' + $relative)
        }
    }
    $pythonCmd = Get-Command 'python' -ErrorAction SilentlyContinue
    if ($null -eq $pythonCmd) { throw 'PYTHON_NOT_FOUND: Install Python 3.10+ and add to PATH.' }
    $dotnetCmd = Get-Command 'dotnet' -ErrorAction SilentlyContinue
    if ($null -eq $dotnetCmd) { throw 'DOTNET_NOT_FOUND: Install .NET SDK 10 x64.' }
    $py = $pythonCmd.Source
    $dn = $dotnetCmd.Source
    Set-Location $root
    Gate 'Python dependencies (opencv-python, numpy, pytest)' $py @('python/tools/check_dependencies.py')
    Gate 'Python unit and source regression tests' $py @('-m','pytest','-q','python/tests')
    Gate '.NET 10 SDK version' $dn @('--version')
    Gate 'C# Release CLI build' $dn @('build','csharp/GomokuVision/GomokuVision.csproj','-c','Release','--nologo')
    Gate 'C# tactical/calibration self-tests' $dn @('run','--no-build','-c','Release','--project','csharp/GomokuVision/GomokuVision.csproj','--','--self-test')
    $base = @('--input','demo/demo.mp4','--calibration','demo/checkerboard_points.csv',
              '--black-template','demo/black.png','--white-template','demo/white.png',
              '--sample-every','2','--full-scan-every','3','--scale','0.5','--white-threshold','0.75')
    $pythonOut = Join-Path $output 'python'
    $csharpOut = Join-Path $output 'csharp'
    Gate 'Python synthetic video recognition (NOT historical video)' $py (@('-m','gomoku','--output-dir',$pythonOut)+$base)
    Gate 'C# synthetic video recognition (NOT historical video)' $dn (@('run','--no-build','-c','Release','--project','csharp/GomokuVision/GomokuVision.csproj','--','--output-dir',$csharpOut)+$base)
    Gate 'Python synthetic result vs known 9-move oracle' $py @('python/tools/verify_synthetic_expected.py',$pythonOut)
    Gate 'C# synthetic result vs known 9-move oracle' $py @('python/tools/verify_synthetic_expected.py',$csharpOut)
    Gate 'Python and C# move sequence / winner parity' $py @('python/tools/compare_runs.py',$pythonOut,$csharpOut)
    Gate 'Synthetic engine descriptive timing report' $py @('python/tools/summarize_engine_performance.py',$pythonOut,$csharpOut,(Join-Path $output 'engine-comparison.json'))
    if (-not $SkipWpfBuild) {
        $wpfAttempted = $true
        Gate 'WPF Release build (does NOT launch video analysis)' $dn @('build','csharp/GomokuVision.Desktop/GomokuVision.Desktop.csproj','-c','Release','--nologo')
    }
    $exitStatus = 0
    LogText 'QUICK_ENGINE_GATE_PASS: Python + C# synthetic video and parity checked.'
    if ($SkipWpfBuild) { LogText 'WPF_BUILD_SKIPPED: WPF is NOT verified by this run.' }
    else { LogText 'WPF_BUILD_PASS: compilation only; GUI runtime acceptance is separate.' }
}
catch {
    $failed = $_.Exception.Message
    LogText ('QUICK_ENGINE_GATE_FAIL: ' + $failed)
}
finally {
    $payload = [ordered]@{
        project='GomokuVision'; version='0.3.3'; mode='synthetic_only'
        historical_video_reprocessed=$false
        outcome= $(if ($exitStatus -eq 0) {'PASS'} else {'FAIL'})
        wpf_build_tested=$wpfAttempted
        started_at=$started.ToString('o')
        ended_at=(Get-Date).ToString('o')
        steps=@($checks.ToArray())
        error=$failed
        log=$log
        outputs=$output
        notice='Passing this test does not establish historical video accuracy or interactive WPF GUI correctness.'
    }
    $payload | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $report -Encoding UTF8
    $payload | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $latest -Encoding UTF8
    LogText ('Report: ' + $report)
    LogText ('Log: ' + $log)
}
exit $exitStatus
