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
    Write-Output 'BUN_MISSING: 需要 bun（Cherry Studio 自带）或 Node.js'
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
    Write-Output 'UV_MISSING: 跳过 Python 依赖（lxml/defusedxml），校验与批注脚本将不可用'
}

# 3) Optional: LibreOffice for PDF rendering / .doc conversion
$soffice = Get-Command soffice -ErrorAction SilentlyContinue
if (-not $soffice) {
    Write-Output 'NOTE: 未检测到 LibreOffice，PDF 渲染验证与 .doc 转换不可用（不影响生成 .docx）'
}

Write-Output 'SETUP_OK'
