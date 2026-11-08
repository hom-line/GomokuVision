$ErrorActionPreference='Stop'
$root=(Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$manifest=Get-Content -LiteralPath (Join-Path $root 'RELEASE_MANIFEST.json') -Raw -Encoding UTF8 | ConvertFrom-Json
$bad=0
foreach($item in $manifest.files){
    $file=Join-Path $root $item.path
    if(-not (Test-Path -LiteralPath $file)) {Write-Host ('MISSING: '+$item.path) -ForegroundColor Red; $bad++; continue}
    $sha=(Get-FileHash -LiteralPath $file -Algorithm SHA256).Hash.ToLowerInvariant()
    if($sha -ne $item.sha256) {Write-Host ('MISMATCH: '+$item.path) -ForegroundColor Red; $bad++}
}
if($bad) {Write-Host ('BUNDLE_INTEGRITY_FAIL: '+$bad) -ForegroundColor Red; exit 1}
Write-Host ('BUNDLE_INTEGRITY_PASS: '+$manifest.files.Count+' files; no video analysis executed.') -ForegroundColor Green
exit 0
