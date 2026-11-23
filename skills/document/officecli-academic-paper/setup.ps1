# setup.ps1 — dependency check for officecli-academic-paper.
# This skill is a scene layer over officecli-docx and needs the officecli CLI.
# The CLI is NOT installed automatically: review the upstream installer first.

$cli = Get-Command officecli -ErrorAction SilentlyContinue
if (-not $cli) {
    Write-Output 'OFFICECLI_MISSING'
    Write-Output '安装方式（任选其一）：'
    Write-Output '  1) winget / 官网安装包：https://github.com/iOfficeAI/OfficeCLI/releases'
    Write-Output '  2) PowerShell: irm https://d.officecli.ai/install.ps1 | iex   （执行前请先审阅脚本）'
    Write-Output '另外需要先安装技能：officecli-docx'
    exit 1
}

officecli --version
Write-Output 'SETUP_OK'
