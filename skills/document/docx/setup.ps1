# setup.ps1 — one-time dependency setup for the docx skill.
# Installs: docx-js (bun) + Python helpers (lxml, defusedxml). Safe to re-run.

$skillDir = $PSScriptRoot
$venv = Join-Path $skillDir 'venv'
$py = Join-Path $venv 'Scripts\python.exe'
$mirror = 'https://pypi.tuna.tsinghua.edu.cn/simple'

Write-Output "skill dir: $skillDir"

# 1) JS: docx-js (used for creating documents)
$bun = Get-Command bun -ErrorAction SilentlyContinue
if (-not $bun) {
    Write-Output 'BUN_MISSING: bun is required (bundled with Cherry Studio) or install Node.js'
    exit 1
}
Push-Location $skillDir
bun add docx --registry https://registry.npmmirror.com
$code = $LASTEXITCODE
Pop-Location
if ($code -ne 0) { Write-Output 'DOCX_NPM_INSTALL_FAILED'; exit 1 }

# 2) Python: helpers for validation / comments / tracked changes
$uv = Get-Command uv -ErrorAction SilentlyContinue
if ($uv) {
    if (-not (Test-Path $py)) {
        uv venv "$venv" --python 3.12
    }
    uv pip install --python "$py" lxml defusedxml --index-url $mirror
} else {
    Write-Output 'UV_MISSING: skipping Python deps (lxml/defusedxml); validation and comment scripts will be unavailable'
}

# 3) Optional: LibreOffice for PDF rendering / .doc conversion
$soffice = Get-Command soffice -ErrorAction SilentlyContinue
if (-not $soffice) {
    Write-Output 'NOTE: LibreOffice not found; PDF rendering verification and .doc conversion are unavailable (docx generation is unaffected)'
}

Write-Output 'SETUP_OK'
