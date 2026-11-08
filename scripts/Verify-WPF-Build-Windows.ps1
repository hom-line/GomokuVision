[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'
$root = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$project = Join-Path $root 'csharp\GomokuVision.Desktop\GomokuVision.Desktop.csproj'
$core = Join-Path $root 'csharp\GomokuVision\GomokuVision.csproj'
$logFolder = if ($env:LOCALAPPDATA) { Join-Path $env:LOCALAPPDATA 'GomokuVision\Logs' } else { Join-Path $root '.logs' }
New-Item -ItemType Directory -Path $logFolder -Force | Out-Null
$log = Join-Path $logFolder ('wpf-build-' + (Get-Date -Format 'yyyyMMdd-HHmmss') + '.log')
function WriteLog([string]$message) {
    Write-Host $message
    Add-Content -LiteralPath $log -Value $message -Encoding UTF8
}
try {
    Set-Location $root
    WriteLog ('Project: ' + $root)
    WriteLog ('Log: ' + $log)
    if (-not (Get-Command dotnet -ErrorAction SilentlyContinue)) { throw '.NET 10 SDK not found in PATH.' }
    WriteLog ('SDKs: ' + ((& dotnet --list-sdks) -join '; '))
    $coreText = Get-Content -LiteralPath $core -Raw -Encoding UTF8
    if ($coreText -match 'Include="OpenCvSharp4.Windows"') { throw 'OLD_PACKAGE_REFERENCES_FOUND: Please extract the complete V0.2.2 archive into a new directory.' }
    if ($coreText -notmatch 'Include="OpenCvSharp4.runtime.win"') { throw 'OpenCvSharp runtime dependency missing.' }
    $detectorPath = Join-Path $root 'csharp\GomokuVision\VisionDetector.cs'
    $detectorText = Get-Content -LiteralPath $detectorPath -Raw -Encoding UTF8
    if ($detectorText -match 'double\[\] scores = \[\-1\.\s*,\s*\-1\.\]') {
        throw 'CS1001_SOURCE_REGRESSION: Replace invalid scores literals [-1.,-1.] with [-1.0,-1.0] in VisionDetector.cs.'
    }
    WriteLog 'V0.2.3 C# source regression preflight PASS.'
    WriteLog 'Restoring .NET 10 WPF project (does not run video analysis)...'
    & dotnet restore $project --force --nologo -v:minimal 2>&1 | Tee-Object -FilePath $log -Append | Out-Host
    if ($LASTEXITCODE -ne 0) { throw ('NuGet restore failed, exit ' + $LASTEXITCODE) }
    WriteLog 'Building Release WPF project (no video processing)...'
    & dotnet build $project -c Release --no-restore --nologo -v:minimal 2>&1 | Tee-Object -FilePath $log -Append | Out-Host
    if ($LASTEXITCODE -ne 0) { throw ('WPF build failed, exit ' + $LASTEXITCODE) }
    WriteLog 'WPF_BUILD_PASS (compile only; interactive GUI NOT verified).'
    exit 0
}
catch {
    WriteLog ('WPF_BUILD_FAIL: ' + $_.Exception.Message)
    WriteLog ('See log: ' + $log)
    exit 1
}
