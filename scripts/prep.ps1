# prep.ps1 - pre-maintenance sync for the cherryuse repo.
#
# This repo is maintained from more than one workstation. Run this BEFORE
# editing anything: it brings the local clone up to date with origin, parks
# uncommitted edits out of the way while it does so, and reports whether the
# installed skills (%APPDATA%\CherryStudio\Data\Skills) match the repo.
#
# Usage:
#   powershell -ExecutionPolicy Bypass -File scripts\prep.ps1
#   powershell -ExecutionPolicy Bypass -File scripts\prep.ps1 -NoStash    # refuse to stash, just fail on a dirty tree
#   powershell -ExecutionPolicy Bypass -File scripts\prep.ps1 -SkipDrift  # skip the installed-skill comparison
#   powershell -ExecutionPolicy Bypass -File scripts\prep.ps1 -Repo D:\path\to\clone
#
# If the script itself is missing from the local clone (for example right after a
# hard reset to an older commit), fetch a copy and run it from anywhere:
#   git show origin/main:scripts/prep.ps1 > "$env:TEMP\prep.ps1"
#   powershell -ExecutionPolicy Bypass -File "$env:TEMP\prep.ps1" -Repo .
#
# Exit codes:
#   0  local clone matches origin, safe to edit
#   1  not a git repo / detached HEAD / no upstream / fetch failed
#   2  rebase conflict - needs a human, nothing was lost
#   3  dirty tree and -NoStash was given
#
# Output stays ASCII on purpose: PowerShell 5.1 misreads non-BOM UTF-8 scripts.

param(
    [switch]$NoStash,
    [switch]$SkipDrift,
    [string]$Repo
)

$ErrorActionPreference = 'Continue'

function Invoke-Git {
    param([string[]]$GitArgs)
    $out = & git @GitArgs 2>&1
    return [pscustomobject]@{ Code = $LASTEXITCODE; Lines = @($out) }
}

function Show-GitResult {
    param($Result)
    foreach ($l in $Result.Lines) { if ("$l".Trim()) { Write-Output ("    " + "$l".Trim()) } }
}

# --- locate the repo ---------------------------------------------------------
# Probe order: -Repo, the script's own folder, the current directory. The middle
# one fails when this script is run from a copy outside the repo (for example a
# copy fetched with "git show origin/main:scripts/prep.ps1" while behind).
$candidates = @()
if ($Repo) { $candidates += $Repo }
if ($PSScriptRoot) { $candidates += $PSScriptRoot }
if ($PWD) { $candidates += $PWD.Path }
$root = $null
foreach ($cand in $candidates) {
    $probe = Invoke-Git @('-C', $cand, 'rev-parse', '--show-toplevel')
    if ($probe.Code -eq 0) {
        $root = ($probe.Lines | Select-Object -First 1).Trim()
        break
    }
}
if (-not $root) {
    Write-Output 'PREP_FAIL: no git repository found from the script folder or the current directory'
    Write-Output 'hint   : pass -Repo <path-to-clone> or run it from inside the clone'
    exit 1
}
Set-Location $root
Write-Output "repo   : $root"

# --- which branch are we on --------------------------------------------------
$br = Invoke-Git @('rev-parse', '--abbrev-ref', 'HEAD')
$branch = ($br.Lines | Select-Object -First 1).Trim()
if (-not $branch -or $branch -eq 'HEAD') {
    Write-Output 'PREP_FAIL: detached HEAD, check out a branch first'
    exit 1
}
$upstream = "origin/$branch"
Write-Output "branch : $branch"

# --- park local edits --------------------------------------------------------
$st = Invoke-Git @('status', '--porcelain')
$dirty = @($st.Lines | Where-Object { "$_".Trim() })
$stashed = $false
if ($dirty.Count -gt 0) {
    Write-Output "local  : $($dirty.Count) uncommitted path(s) - these never reached origin"
    foreach ($line in $dirty) { Write-Output ("    " + "$line".Trim()) }
    if ($NoStash) {
        Write-Output 'PREP_FAIL: dirty tree and -NoStash given; commit, discard or rerun without -NoStash'
        exit 3
    }
    $msg = 'prep-autostash ' + (Get-Date -Format 'yyyy-MM-dd HH:mm:ss')
    $sp = Invoke-Git @('stash', 'push', '--include-untracked', '-m', $msg)
    if ($sp.Code -ne 0) {
        Write-Output 'PREP_FAIL: git stash failed, nothing was changed'
        Show-GitResult $sp
        exit 1
    }
    $stashed = $true
    Write-Output "local  : parked in stash as [$msg]"
}

# --- fetch -------------------------------------------------------------------
$fetch = Invoke-Git @('fetch', '--prune', 'origin')
if ($fetch.Code -ne 0) {
    Write-Output 'PREP_FAIL: git fetch failed (network, or expired credential)'
    Show-GitResult $fetch
    if ($stashed) { Write-Output 'note   : your edits are still in the stash, run: git stash pop' }
    exit 1
}

# --- compare with origin -----------------------------------------------------
$count = Invoke-Git @('rev-list', '--left-right', '--count', "HEAD...$upstream")
if ($count.Code -ne 0) {
    Write-Output "PREP_FAIL: no upstream branch $upstream (was the branch renamed or never pushed?)"
    if ($stashed) { Write-Output 'note   : your edits are still in the stash, run: git stash pop' }
    exit 1
}
$parts = ("$($count.Lines[0])".Trim() -split '\s+')
$ahead = [int]$parts[0]
$behind = [int]$parts[1]
Write-Output "remote : $ahead local commit(s) not pushed, $behind commit(s) to pull"

if ($behind -gt 0 -and $ahead -eq 0) {
    $m = Invoke-Git @('merge', '--ff-only', $upstream)
    if ($m.Code -ne 0) {
        Write-Output 'PREP_FAIL: fast-forward failed'
        Show-GitResult $m
        if ($stashed) { Write-Output 'note   : your edits are still in the stash, run: git stash pop' }
        exit 1
    }
    Write-Output "pull   : fast-forwarded $behind commit(s)"
    Show-GitResult $m
}
elseif ($behind -gt 0 -and $ahead -gt 0) {
    Write-Output 'pull   : branches diverged, rebasing local commits onto origin'
    $rb = Invoke-Git @('rebase', $upstream)
    if ($rb.Code -ne 0) {
        $ab = Invoke-Git @('rebase', '--abort')
        Write-Output 'PREP_FAIL: rebase conflict - local commits are untouched after the abort'
        Write-Output "next   : resolve by hand (git rebase origin/$branch), or reset to origin and redo the work"
        if ($stashed) { Write-Output 'note   : your edits are still in the stash, run: git stash pop' }
        exit 2
    }
    Write-Output 'pull   : rebase clean'
}
elseif ($ahead -gt 0) {
    Write-Output 'warn   : local commits exist that origin does not have - push them before starting new work'
}
else {
    Write-Output 'pull   : already up to date'
}

# --- put the edits back ------------------------------------------------------
if ($stashed) {
    $pop = Invoke-Git @('stash', 'pop')
    if ($pop.Code -ne 0) {
        Write-Output 'PREP_WARN: could not restore the stash (probably conflicts with pulled changes)'
        Show-GitResult $pop
        Write-Output 'next   : your edits are safe in the stash; run "git stash list" then "git stash pop" and merge by hand'
    }
    else {
        Write-Output 'local  : uncommitted edits restored'
    }
}

# --- does the installed copy match the repo? --------------------------------
if (-not $SkipDrift) {
    $skillsRoot = Join-Path $env:APPDATA 'CherryStudio\Data\Skills'
    if (-not (Test-Path $skillsRoot)) {
        Write-Output "drift  : skipped, $skillsRoot not found"
    }
    else {
        $repoSkills = Join-Path $root 'skills'
        $manifests = @(Get-ChildItem -Path $repoSkills -Recurse -Filter 'SKILL.md' -File -ErrorAction SilentlyContinue)
        $missing = 0; $drift = 0; $same = 0
        foreach ($m in $manifests) {
            $name = Split-Path -Leaf (Split-Path -Parent $m.FullName)
            $installed = Join-Path $skillsRoot (Join-Path $name 'SKILL.md')
            if (-not (Test-Path $installed)) {
                Write-Output "drift  : [not installed] $name"
                $missing++
            }
            elseif ((Get-FileHash $m.FullName -Algorithm SHA256).Hash -ne (Get-FileHash $installed -Algorithm SHA256).Hash) {
                Write-Output "drift  : [repo differs] $name"
                $drift++
            }
            else { $same++ }
        }
        Write-Output "drift  : $same in sync, $drift differ, $missing not installed (of $($manifests.Count))"
        if ($drift -gt 0 -or $missing -gt 0) {
            Write-Output 'note   : the repo is the source of truth; reinstall the named skill to apply repo changes'
        }
    }
}

# --- summary -----------------------------------------------------------------
$head = Invoke-Git @('log', '-1', '--format=%h %s')
$short = ($head.Lines | Select-Object -First 1).Trim()
Write-Output ''
Write-Output "HEAD   : $short"
Write-Output 'PREP_OK'
exit 0
