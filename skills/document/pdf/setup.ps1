# setup.ps1 - one-time dependency setup for the pdf skill.
# Installs Python PDF libraries. OCR additionally needs tesseract + poppler binaries.

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

uv pip install --python "$py" pypdf pdfplumber reportlab pypdfium2 pillow pytesseract pdf2image --index-url $mirror
if ($LASTEXITCODE -ne 0) { Write-Output 'DEPS_FAILED'; exit 1 }

& $py -c "import pypdf, pdfplumber, reportlab, pypdfium2; print('SETUP_OK')"

Write-Output 'NOTE: OCR (pytesseract/pdf2image) also needs tesseract and poppler installed system-wide'
