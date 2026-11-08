[CmdletBinding()]
param([switch]$NoBuild)
$ErrorActionPreference = 'Stop'
$root = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$project = Join-Path $root 'csharp\GomokuVision.Desktop\GomokuVision.Desktop.csproj'
$exe = Join-Path $root 'csharp\GomokuVision.Desktop\bin\Release\net10.0-windows\GomokuVision.Desktop.exe'
$viewer = Join-Path $root 'index.html'
if ($env:LOCALAPPDATA) { $logFolder = Join-Path $env:LOCALAPPDATA 'GomokuVision\Logs' }
else { $logFolder = Join-Path $root '.logs' }
New-Item -ItemType Directory -Path $logFolder -Force | Out-Null
$log = Join-Path $logFolder ('launch-' + (Get-Date -Format 'yyyyMMdd-HHmmss') + '.log')
function Log([string]$s) {
    Add-Content -LiteralPath $log -Value $s -Encoding UTF8
    Write-Host $s
}
try {
    Log ('Project: ' + $root)
    Log ('Date: ' + (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'))
    Log ('OS: ' + [Environment]::OSVersion.VersionString)
    if (-not (Test-Path -LiteralPath $project)) { throw 'WPF project missing: ' + $project }
    $fullVideo = Join-Path $root 'demo\full_game\full_game_961.mp4'
    if (-not (Test-Path -LiteralPath $fullVideo)) {
        $python = Get-Command python -ErrorAction SilentlyContinue
        if (-not $python) { throw 'Demo MP4 is packed (.xz). Install Python 3 and run python python/tools/restore_demo_videos.py.' }
        Log 'Restoring the original synthetic 961-frame video from lossless .xz archive.'
        & $python.Source (Join-Path $root 'python\tools\restore_demo_videos.py') --only full_game_961.mp4 --verify 2>&1 |
            Tee-Object -FilePath $log -Append | Out-Host
        if ($LASTEXITCODE -ne 0) { throw 'Demo video restore failed: SHA verification failed or archive missing.' }
    }

    $cmd = Get-Command dotnet.exe -ErrorAction SilentlyContinue
    if (-not $cmd) { $cmd = Get-Command dotnet -ErrorAction SilentlyContinue }
    if ($NoBuild -and -not (Test-Path -LiteralPath $exe)) {
        throw '-NoBuild requested but compiled WPF executable was not found.'
    }
    if (-not (Test-Path -LiteralPath $exe) -or (-not $NoBuild -and $cmd)) {
        if (-not $cmd) {
            throw 'Missing .NET 10 SDK / dotnet command. Install .NET 10 SDK (x64). Cached results can still be viewed without .NET.'
        }
        $sdks = (& $cmd.Source --list-sdks 2>&1 | Out-String).Trim()
        Log ('Installed SDKs: ' + $sdks)
        if ($sdks -notmatch '(?m)^10\.') {
            throw '.NET 10 SDK was not found. Install .NET SDK 10 x64, not only .NET Runtime.'
        }
        Log 'Building Windows WPF application. First restore requires NuGet access if packages are not cached.'
        & $cmd.Source build $project -c Release --nologo -v:minimal 2>&1 |
            Tee-Object -FilePath $log -Append | Out-Host
        $buildCode = $LASTEXITCODE
        if ($buildCode -ne 0) { throw ('WPF build failed (exit ' + $buildCode + '). Read build errors in the log.') }
    }
    if (-not (Test-Path -LiteralPath $exe)) { throw ('Build completed but executable is missing: ' + $exe) }
    Log ('Launching: ' + $exe)
    $p = Start-Process -FilePath $exe -WorkingDirectory $root -PassThru -ErrorAction Stop
    Start-Sleep -Seconds 4
    $p.Refresh()
    if ($p.HasExited) {
        throw ('WPF exited within 4 seconds, code ' + $p.ExitCode + '. Check %LOCALAPPDATA%\GomokuVision\Logs\desktop-errors.log')
    }
    Log ('WPF process is running (PID ' + $p.Id + '). No video analysis has been triggered.')
    Log ('Launch diagnostics: ' + $log)
    exit 0
}
catch {
    Log ('LAUNCH_ERROR: ' + $_.Exception.Message)
    Log ('Launch diagnostics: ' + $log)
    Log 'WPF GUI is NOT verified / NOT started. See docs/WINDOWS_STARTUP_TROUBLESHOOTING_zh_TW.md'
    if (Test-Path -LiteralPath $viewer) {
        try {
            Start-Process -FilePath $viewer -ErrorAction Stop
            Log 'Opened the offline VERIFIED RESULTS viewer instead (read-only, not WPF).'
        } catch { Log ('Could not open viewer: ' + $_.Exception.Message) }
    }
    exit 1
}
