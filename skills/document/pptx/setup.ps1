# setup.ps1 - one-time dependency setup for the pptx skill.
# Installs pptxgenjs (bun) + Python helpers (python-pptx, Pillow, defusedxml, lxml).

$skillDir = $PSScriptRoot
$venv = Join-Path $skillDir 'venv'
$py = Join-Path $venv 'Scripts\python.exe'
$mirror = 'https://pypi.tuna.tsinghua.edu.cn/simple'

$bun = Get-Command bun -ErrorAction SilentlyContinue
if (-not $bun) {
    Write-Output 'BUN_MISSING: bun is required (bundled with Cherry Studio) or install Node.js'
    exit 1
}
Push-Location $skillDir
bun add pptxgenjs --registry https://registry.npmmirror.com
$code = $LASTEXITCODE
Pop-Location
if ($code -ne 0) { Write-Output 'PPTXGENJS_INSTALL_FAILED'; exit 1 }

$uv = Get-Command uv -ErrorAction SilentlyContinue
if (-not $uv) {
    Write-Output 'UV_MISSING: skipping Python deps (python-pptx etc.)'
    exit 1
}
if (-not (Test-Path $py)) {
    uv venv "$venv" --python 3.12
}
uv pip install --python "$py" python-pptx pillow defusedxml lxml --index-url $mirror
if ($LASTEXITCODE -ne 0) { Write-Output 'DEPS_FAILED'; exit 1 }

& $py -c "import pptx, PIL, defusedxml, lxml; print('SETUP_OK')"
