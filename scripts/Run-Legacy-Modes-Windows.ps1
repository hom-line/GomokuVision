param([switch]$IncludeMatlab)
$ErrorActionPreference = 'Stop'
$root=(Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$stamp=(Get-Date -Format 'yyyyMMdd-HHmmss')
$out=Join-Path $env:LOCALAPPDATA ("GomokuVision\Gates\legacy-modes-"+$stamp)
New-Item -ItemType Directory -Path $out -Force | Out-Null
$log=Join-Path $out 'legacy-modes.log'
function Record([string]$text) {
    Write-Host $text
    Add-Content -LiteralPath $log -Value $text -Encoding UTF8
}
function CheckExit([string]$name) {
    if ($LASTEXITCODE -ne 0) { throw ($name+' exit code '+$LASTEXITCODE+'; report '+$log) }
    Record ('PASS: '+$name)
}
$py=(Get-Command python -ErrorAction Stop).Source
$dotnet=(Get-Command dotnet -ErrorAction Stop).Source
$demo=Join-Path $root 'demo'
$project=Join-Path $root 'csharp\GomokuVision\GomokuVision.csproj'
Record 'GomokuVision V0.3.6 LEGACY MODE GATE - synthetic 9-move data only'
Record ('Evidence directory: '+$out)
# Build once. The recognizer runs in its own C# process; no Python proxy.
& $dotnet build $project -c Release --nologo
CheckExit 'C# Release build'
$base=@('--input',(Join-Path $demo 'demo.mp4'), '--calibration',(Join-Path $demo 'checkerboard_points.csv'),
        '--black-template',(Join-Path $demo 'black.png'),'--white-template',(Join-Path $demo 'white.png'),
        '--sample-every','6','--confirmations','2','--scale','0.5')
foreach ($roi in @('separated','shared')) {
    foreach ($view in @('recognition','recognition_prediction')) {
        foreach ($engine in @('python','csharp')) {
            $dest=Join-Path $out ("$engine-$roi-$view")
            New-Item -ItemType Directory -Path $dest -Force | Out-Null
            $arguments=$base+@('--output-dir',$dest,'--roi-mode',$roi,'--overlay-mode',$view)
            Record ("RUN $engine ROI=$roi overlay=$view")
            if ($engine -eq 'python') {
                $env:PYTHONPATH=Join-Path $root 'python'
                & $py -m gomoku @arguments
            } else {
                & $dotnet run --project $project -c Release --no-build -- @arguments
            }
            CheckExit ("$engine $roi $view")
            & $py (Join-Path $root 'python\tools\verify_synthetic_expected.py') $dest
            CheckExit ("$engine $roi $view nine-move oracle")
        }
        $p=Join-Path $out ("python-$roi-$view")
        $c=Join-Path $out ("csharp-$roi-$view")
        & $py (Join-Path $root 'python\tools\compare_runs.py') $p $c
        CheckExit ("Python/C# parity $roi $view")
    }
}
if ($IncludeMatlab) {
    $matlab=$env:GOMOKUVISION_MATLAB_EXE
    if ([string]::IsNullOrWhiteSpace($matlab)) {
        $cmd=Get-Command matlab -ErrorAction SilentlyContinue
        if ($null -eq $cmd) {throw 'MATLAB not found (required by -IncludeMatlab).'}
        $matlab=$cmd.Source
    }
    $matlabDir=Join-Path $root 'matlab\modern'
    foreach($roi in @('separated','shared')) {
        foreach($view in @('recognition','recognition_prediction')) {
            $dest=Join-Path $out ("matlab-$roi-$view")
            & $py (Join-Path $root 'python\tools\make_matlab_gate_config.py') $dest $roi $view
            CheckExit 'MATLAB config generation'
            $matlabEsc=$matlabDir.Replace("'","''")
            $configEsc=(Join-Path $dest 'matlab-gate-config.json').Replace("'","''")
            & $matlab -batch ("addpath('"+$matlabEsc+"'); gomoku_batch('"+$configEsc+"')")
            CheckExit ("MATLAB $roi $view")
            & $py (Join-Path $root 'python\tools\verify_synthetic_expected.py') $dest
            CheckExit ("MATLAB oracle $roi $view")
            & $py (Join-Path $root 'python\tools\compare_runs.py') (Join-Path $out ("python-$roi-$view")) $dest
            CheckExit ("Python/MATLAB parity $roi $view")
        }
    }
}
Record 'V036_LEGACY_MODES_PASS'
Record ('Logs and output: '+$out)
exit 0
