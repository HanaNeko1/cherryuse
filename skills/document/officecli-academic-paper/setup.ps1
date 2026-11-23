# setup.ps1 - install/check the officecli CLI required by this skill.
#
# Usage:
#   powershell -ExecutionPolicy Bypass -File setup.ps1            # check only
#   powershell -ExecutionPolicy Bypass -File setup.ps1 -Install   # download from GitHub releases
#
# This skill is a scene layer over officecli-docx: install that skill too.
# Windows only. For macOS/Linux see DEPLOY.md in the repository root.

param([switch]$Install)

$installDir = Join-Path $env:LOCALAPPDATA 'Programs\officecli'
$exe = Join-Path $installDir 'officecli.exe'
$repo = 'iOfficeAI/OfficeCLI'

function Find-OfficeCli {
    $cmd = Get-Command officecli -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }
    if (Test-Path $exe) { return $exe }
    return $null
}

$found = Find-OfficeCli
if ($found) {
    & $found --version
    Write-Output 'SETUP_OK'
    exit 0
}

if (-not $Install) {
    Write-Output 'OFFICECLI_MISSING'
    Write-Output 'Run with -Install to download the official GitHub release:'
    Write-Output ('  powershell -ExecutionPolicy Bypass -File "' + $PSCommandPath + '" -Install')
    Write-Output "Manual download: https://github.com/$repo/releases"
    exit 1
}

Write-Output "Downloading latest officecli release from github.com/$repo ..."
$headers = @{ 'User-Agent' = 'cherryuse-setup' }
$rel = Invoke-RestMethod "https://api.github.com/repos/$repo/releases/latest" -Headers $headers

$asset = $rel.assets | Where-Object { $_.name -eq 'officecli-win-x64.exe' } | Select-Object -First 1
if (-not $asset) { Write-Output 'ASSET_NOT_FOUND: officecli-win-x64.exe'; exit 1 }

New-Item -ItemType Directory -Force $installDir | Out-Null
$tmp = Join-Path $installDir 'officecli-win-x64.exe'
Invoke-WebRequest $asset.browser_download_url -OutFile $tmp

$sumsAsset = $rel.assets | Where-Object { $_.name -eq 'SHA256SUMS' } | Select-Object -First 1
if ($sumsAsset) {
    $sums = (Invoke-WebRequest $sumsAsset.browser_download_url -UseBasicParsing).Content
    $line = ($sums -split "`n") | Where-Object { $_ -match 'officecli-win-x64\.exe' } | Select-Object -First 1
    if ($line) {
        $expected = ($line.Trim() -split '\s+')[0].ToLower()
        $actual = (Get-FileHash $tmp -Algorithm SHA256).Hash.ToLower()
        if ($expected -ne $actual) {
            Write-Output "CHECKSUM_MISMATCH expected=$expected actual=$actual"
            exit 1
        }
        Write-Output 'CHECKSUM_OK'
    }
}

Move-Item -Force $tmp $exe

$p = [Environment]::GetEnvironmentVariable('Path','User')
if (-not $p) { $p = '' }
if ($p -notmatch [regex]::Escape($installDir)) {
    if ($p -and -not $p.EndsWith(';')) { $p = $p + ';' }
    [Environment]::SetEnvironmentVariable('Path', $p + $installDir, 'User')
    Write-Output "PATH_ADDED $installDir (open a new terminal to use 'officecli' directly)"
}

& $exe --version
Write-Output 'SETUP_OK'
