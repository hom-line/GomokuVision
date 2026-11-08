param(
    [switch]$SkipDotnet,
    [switch]$SkipGuiBuild
)
$ErrorActionPreference = 'Stop'
$root = Split-Path $PSScriptRoot -Parent
Set-Location $root
function RunChecked([string]$Label, [scriptblock]$Script) {
    Write-Host "`n>>> $Label" -ForegroundColor Cyan
    & $Script
    if ($LASTEXITCODE -ne 0) { throw "GATE_FAILED: $Label (exit $LASTEXITCODE)" }
}

RunChecked 'Install Python requirements' { python -m pip install -r .\python\requirements-dev.txt }
$env:PYTHONPATH = (Join-Path $root 'python')
RunChecked 'Python unit / integration tests' { python -m pytest -q .\python\tests }
RunChecked 'Generate owned synthetic benchmark' { python .\python\tools\make_demo.py .\demo }
RunChecked 'Python end-to-end video' {
    python -m gomoku --input .\demo\demo.mp4 `
      --calibration .\demo\checkerboard_points.csv `
      --black-template .\demo\black.png --white-template .\demo\white.png `
      --output-dir .\results\python --sample-every 2 --full-scan-every 3 `
      --scale .5 --white-threshold .75
}
if ($SkipDotnet) {
    Write-Host 'PYTHON_ONLY_PASS (C# and WPF NOT VERIFIED)' -ForegroundColor Yellow
    exit 0
}
RunChecked 'Verify .NET 10 SDK' { dotnet --version }
RunChecked 'C# native CLI build' { dotnet build .\csharp\GomokuVision\GomokuVision.csproj -c Release }
RunChecked 'C# core tactical self-tests' { dotnet run -c Release --no-build --project .\csharp\GomokuVision\GomokuVision.csproj -- --self-test }
RunChecked 'C# end-to-end video' {
    dotnet run -c Release --no-build --project .\csharp\GomokuVision\GomokuVision.csproj -- `
      --input .\demo\demo.mp4 --calibration .\demo\checkerboard_points.csv `
      --black-template .\demo\black.png --white-template .\demo\white.png `
      --output-dir .\results\csharp --sample-every 2 --full-scan-every 3 --scale .5 --white-threshold .75
}
RunChecked 'Two-engine move parity' { python .\python\tools\compare_runs.py .\results\python .\results\csharp }
if (-not $SkipGuiBuild) {
    RunChecked 'WPF GUI Release build' { dotnet build .\csharp\GomokuVision.Desktop\GomokuVision.Desktop.csproj -c Release }
    Write-Host 'WPF_BUILD_PASS (interactive Windows GUI acceptance is separate)' -ForegroundColor Green
}
Write-Host 'ALL_LOCAL_AUTOMATED_GATES_PASS' -ForegroundColor Green
