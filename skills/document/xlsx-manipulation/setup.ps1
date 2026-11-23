# setup.ps1 - one-time dependency setup for the xlsx-manipulation skill.

$skillDir = $PSScriptRoot
$venv = Join-Path $skillDir 'venv'
$py = Join-Path $venv 'Scripts\python.exe'
$mirror = 'https://pypi.tuna.tsinghua.edu.cn/simple'

$uv = Get-Command uv -ErrorAction SilentlyContinue
if (-not $uv) {
    Write-Output 'UV_MISSING: install uv first (winget install --id=astral-sh.uv -e)'
    exit 1
}

if (-not (Test-Path $py)) {
    uv venv "$venv" --python 3.12
}

uv pip install --python "$py" openpyxl --index-url $mirror
if ($LASTEXITCODE -ne 0) { Write-Output 'DEPS_FAILED'; exit 1 }

& $py -c "import openpyxl; print('SETUP_OK', openpyxl.__version__)"
