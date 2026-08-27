$ErrorActionPreference = 'Stop'
$webRoot = Join-Path $PSScriptRoot 'dist'
$python = Get-Command python -ErrorAction Stop
$server = Start-Process -FilePath $python.Source -ArgumentList @('-m', 'http.server', '8765', '--bind', '127.0.0.1', '--directory', $webRoot) -WindowStyle Hidden -PassThru
try {
    Start-Sleep -Milliseconds 800
    $chrome = 'C:\Program Files\Google\Chrome\Application\chrome.exe'
    if (-not (Test-Path -LiteralPath $chrome)) { $chrome = 'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe' }
    Start-Process -FilePath $chrome -ArgumentList @('--new-window', '--start-fullscreen', '--app=http://127.0.0.1:8765/?scene=1&auto=1') -Wait
}
finally {
    Stop-Process -Id $server.Id -ErrorAction SilentlyContinue
}
