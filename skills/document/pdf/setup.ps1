# setup.ps1 - one-time dependency setup for the pdf skill.
#
# Usage:
#   powershell -ExecutionPolicy Bypass -File setup.ps1              # Python libs only
#   powershell -ExecutionPolicy Bypass -File setup.ps1 -InstallOcr  # also install tesseract + poppler
#
# OCR (scanned PDFs) needs the tesseract and poppler system binaries.

param([switch]$InstallOcr)

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

& $py -c "import pypdf, pdfplumber, reportlab, pypdfium2; print('PY_DEPS_OK')"

if (-not $InstallOcr) {
    Write-Output 'NOTE: OCR not installed. Run again with -InstallOcr to add tesseract + poppler.'
    exit 0
}

# --- tesseract ---
$tessDefault = 'C:\Program Files\Tesseract-OCR\tesseract.exe'
$tess = Get-Command tesseract -ErrorAction SilentlyContinue
if (-not $tess -and -not (Test-Path $tessDefault)) {
    Write-Output 'Installing Tesseract OCR via winget ...'
    winget install -e --id UB-Mannheim.TesseractOCR --accept-package-agreements --accept-source-agreements
}

# --- poppler (pdftoppm) ---
$popBase = Join-Path $env:LOCALAPPDATA 'Programs\poppler'
$pdftoppm = Get-Command pdftoppm -ErrorAction SilentlyContinue
$popExe = $null
if ($pdftoppm) {
    $popExe = $pdftoppm.Source
} else {
    $popExe = Get-ChildItem $popBase -Recurse -Filter pdftoppm.exe -ErrorAction SilentlyContinue | Select-Object -First 1
}

if (-not $popExe) {
    Write-Output 'Downloading Poppler from GitHub releases ...'
    $headers = @{ 'User-Agent' = 'cherryuse-setup' }
    $rel = Invoke-RestMethod 'https://api.github.com/repos/oschwartz10612/poppler-windows/releases/latest' -Headers $headers
    $zipAsset = $rel.assets | Where-Object { $_.name -like '*.zip' } | Select-Object -First 1
    if (-not $zipAsset) { Write-Output 'POPPLER_ASSET_NOT_FOUND'; exit 1 }
    New-Item -ItemType Directory -Force $popBase | Out-Null
    $zip = Join-Path $popBase 'poppler.zip'
    Invoke-WebRequest $zipAsset.browser_download_url -OutFile $zip
    Expand-Archive -Path $zip -DestinationPath $popBase -Force
    $popExe = Get-ChildItem $popBase -Recurse -Filter pdftoppm.exe -ErrorAction SilentlyContinue | Select-Object -First 1
}

if ($popExe) {
    $binDir = Split-Path -Parent $popExe.FullName
    $p = [Environment]::GetEnvironmentVariable('Path','User')
    if (-not $p) { $p = '' }
    if ($p -notmatch [regex]::Escape($binDir)) {
        if ($p -and -not $p.EndsWith(';')) { $p = $p + ';' }
        [Environment]::SetEnvironmentVariable('Path', $p + $binDir, 'User')
        Write-Output "PATH_ADDED $binDir (open a new terminal to use pdftoppm directly)"
    }
}

$tessOk = (Get-Command tesseract -ErrorAction SilentlyContinue) -or (Test-Path $tessDefault)
$popOk = $popExe -ne $null
Write-Output ("tesseract: " + $(if ($tessOk) { 'OK' } else { 'MISSING' }))
Write-Output ("poppler:   " + $(if ($popOk) { 'OK' } else { 'MISSING' }))
if ($tessOk -and $popOk) { Write-Output 'OCR_OK' }
