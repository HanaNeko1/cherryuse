# setup.ps1 - dependency check for officecli-academic-paper.
# This skill is a scene layer over officecli-docx and needs the officecli CLI.
# The CLI is NOT installed automatically: review the upstream installer first.

$cli = Get-Command officecli -ErrorAction SilentlyContinue
if (-not $cli) {
    Write-Output 'OFFICECLI_MISSING'
    Write-Output 'Install options:'
    Write-Output '  Release binaries: https://github.com/iOfficeAI/OfficeCLI/releases'
    Write-Output '  PowerShell: irm https://d.officecli.ai/install.ps1 | iex   (review the script first)'
    Write-Output 'Also install the officecli-docx skill first.'
    exit 1
}

officecli --version
Write-Output 'SETUP_OK'
