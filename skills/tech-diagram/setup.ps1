# setup.ps1 — one-time environment setup for the tech-diagram skill.
# Creates a local venv inside the skill folder. Safe to re-run.

$skillDir = $PSScriptRoot
$venv = Join-Path $skillDir 'venv'
$py = Join-Path $venv 'Scripts\python.exe'
$mirror = 'https://pypi.tuna.tsinghua.edu.cn/simple'

Write-Output "skill dir: $skillDir"

$uv = Get-Command uv -ErrorAction SilentlyContinue
if (-not $uv) {
    Write-Output 'UV_MISSING'
    Write-Output 'Install uv first:  winget install --id=astral-sh.uv -e'
    exit 1
}

Write-Output '[1/3] Python 3.12 ...'
uv python install 3.12
if ($LASTEXITCODE -ne 0) { Write-Output 'PYTHON_INSTALL_FAILED'; exit 1 }

Write-Output '[2/3] venv ...'
if (-not (Test-Path $py)) {
    uv venv "$venv" --python 3.12
    if ($LASTEXITCODE -ne 0) { Write-Output 'VENV_FAILED'; exit 1 }
}

Write-Output '[3/3] schemdraw + matplotlib ...'
uv pip install --python "$py" schemdraw matplotlib --index-url $mirror
if ($LASTEXITCODE -ne 0) { Write-Output 'DEPS_FAILED'; exit 1 }

& $py -c "import schemdraw, matplotlib; print('SETUP_OK schemdraw=' + schemdraw.__version__ + ' matplotlib=' + matplotlib.__version__)"
