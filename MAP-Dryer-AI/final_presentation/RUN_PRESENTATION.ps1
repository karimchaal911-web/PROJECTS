<#
.SYNOPSIS
    Launches the soutenance presentation in a clean fullscreen browser window.

.DESCRIPTION
    Serves the pre-built bundle from web\dist with a small zero-dependency Node
    server, waits until the port actually answers, then opens Chrome (or Edge)
    as an app window: no tabs, no address bar, no bookmarks. Nothing is fetched
    from the network.

    Closing this terminal, or pressing Ctrl+C, stops the server.

.PARAMETER Safe
    Start in reduced-performance mode (lower resolution, no shadows, fewer
    particles). Every scene, beat and number is unchanged.

.PARAMETER Port
    Override the loopback port. Defaults to the first free port from 4173.

.EXAMPLE
    .\RUN_PRESENTATION.ps1
    .\RUN_PRESENTATION.ps1 -Safe
#>
[CmdletBinding()]
param(
    [switch]$Safe,
    [int]$Port = 0
)

$ErrorActionPreference = 'Stop'
$web = Join-Path $PSScriptRoot 'web'
$dist = Join-Path $web 'dist'
$serve = Join-Path $web 'scripts\serve.mjs'

if (-not (Get-Command node -ErrorAction SilentlyContinue)) {
    throw 'Node.js is required to serve the presentation. Install Node, or open the PDF fallback.'
}

if (-not (Test-Path (Join-Path $dist 'index.html'))) {
    Write-Host 'No build found. Building once (about 10 seconds)...' -ForegroundColor Yellow
    Push-Location $web
    try {
        if (-not (Test-Path 'node_modules')) { npm install --silent }
        npx vite build
    } finally { Pop-Location }
}

function Get-FreePort {
    param([int]$Start = 4173)
    for ($p = $Start; $p -lt $Start + 40; $p++) {
        $inUse = Get-NetTCPConnection -LocalPort $p -State Listen -ErrorAction SilentlyContinue
        if (-not $inUse) { return $p }
    }
    throw 'No free port found between 4173 and 4212.'
}

if ($Port -eq 0) { $Port = Get-FreePort }

$browser = @(
    'C:\Program Files\Google\Chrome\Application\chrome.exe',
    'C:\Program Files (x86)\Google\Chrome\Application\chrome.exe',
    'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe'
) | Where-Object { Test-Path $_ } | Select-Object -First 1

if (-not $browser) {
    throw 'Chrome or Edge is required. Install one, or use the PDF / PPTX fallback.'
}

Write-Host ''
Write-Host '  INTELLIGENT DIGITALIZATION OF SOLUBLE MAP PRODUCTION' -ForegroundColor Green
Write-Host '  OCP - ENSAM soutenance' -ForegroundColor DarkGray
Write-Host ''
Write-Host "  serving   http://127.0.0.1:$Port"
Write-Host '  controls  -> next   <- back   1-9,0 scenes   Shift+1-4 scenes 11-14'
Write-Host '            F fullscreen   P notes   S safe mode   H help'
Write-Host ''

# --- start the server -------------------------------------------------------
# -WorkingDirectory is explicit: Start-Process does not inherit PowerShell's
# location, and the previous launcher silently started the server in the wrong
# folder.
$outLog = Join-Path $env:TEMP "map-soutenance-server-$Port.log"
$errLog = Join-Path $env:TEMP "map-soutenance-server-$Port.err"
Remove-Item $outLog, $errLog -ErrorAction SilentlyContinue

$server = Start-Process -FilePath 'node' `
    -ArgumentList @($serve, "$Port") `
    -WorkingDirectory $web `
    -PassThru -WindowStyle Hidden `
    -RedirectStandardOutput $outLog -RedirectStandardError $errLog

# --- wait for the port to actually answer -----------------------------------
# The previous launcher slept a fixed three seconds and opened the browser onto
# ERR_CONNECTION_REFUSED when the server took longer.
$ready = $false
for ($i = 0; $i -lt 100; $i++) {
    if ($server.HasExited) { break }
    try {
        $null = Invoke-WebRequest -Uri "http://127.0.0.1:$Port/" -UseBasicParsing -TimeoutSec 2
        $ready = $true
        break
    } catch {
        Start-Sleep -Milliseconds 200
    }
}

if (-not $ready) {
    $detail = if (Test-Path $errLog) { Get-Content $errLog -Raw } else { '' }
    if (-not $server.HasExited) { Stop-Process -Id $server.Id -Force -ErrorAction SilentlyContinue }
    throw "The presentation server did not start on port $Port.`n$detail"
}

Write-Host '  Server ready. Opening the presentation...' -ForegroundColor Green
if ($Safe) {
    Write-Host '  Safe mode requested - press S once it loads.' -ForegroundColor Yellow
}
Write-Host '  Press F for fullscreen. Ctrl+C here to stop.' -ForegroundColor DarkGray
Write-Host ''

$profileDir = Join-Path $env:TEMP 'map-soutenance-profile'
Start-Process -FilePath $browser -ArgumentList @(
    "--app=http://127.0.0.1:$Port/",
    "--user-data-dir=$profileDir",
    '--start-maximized',
    '--no-first-run',
    '--no-default-browser-check',
    '--disable-features=Translate,MediaRouter',
    '--autoplay-policy=no-user-gesture-required'
) | Out-Null

try {
    Wait-Process -Id $server.Id
} finally {
    if (-not $server.HasExited) {
        Stop-Process -Id $server.Id -Force -ErrorAction SilentlyContinue
    }
    Write-Host '  Server stopped.' -ForegroundColor DarkGray
}
