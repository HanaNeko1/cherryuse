# ensure_imgserver.ps1 — idempotent launcher for the local image server.
#
# Usage:
#   powershell -ExecutionPolicy Bypass -File ensure_imgserver.ps1 -ServeDir "C:\path\to\images" -Port 18080

param(
    [string]$ServeDir = (Get-Location).Path,
    [int]$Port = 18080
)

$skillDir = Split-Path -Parent $PSScriptRoot
$py = Join-Path $skillDir 'venv\Scripts\python.exe'
$server = Join-Path $PSScriptRoot 'imgserver.py'

if (-not (Test-Path $py)) {
    Write-Output 'NO_VENV: run setup.ps1 first'
    exit 1
}

function Get-Ping {
    param([int]$p)
    try {
        $r = Invoke-WebRequest "http://127.0.0.1:$p/_ping" -UseBasicParsing -TimeoutSec 2
        return $r.Content
    } catch {
        return $null
    }
}

$ping = Get-Ping -p $Port
if ($ping) {
    Write-Output "RUNNING $ping"
    Write-Output "EMBED http://127.0.0.1:$Port/"
    exit 0
}

Start-Process -FilePath $py -ArgumentList "`"$server`" --root `"$ServeDir`" --port $Port" -WindowStyle Hidden
Start-Sleep -Seconds 2

$ping = Get-Ping -p $Port
if ($ping) {
    Write-Output "STARTED $ping"
    Write-Output "EMBED http://127.0.0.1:$Port/"
} else {
    Write-Output 'FAILED: server did not start'
    exit 1
}
