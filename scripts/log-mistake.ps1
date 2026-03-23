#Requires -Version 7.0
<#
.SYNOPSIS
    Append a dated mistake entry to .claude/CLAUDE.md

.DESCRIPTION
    Called automatically by Claude Code hooks (Stop, PostToolUse on failure)
    and by the /mistake slash command.

.PARAMETER Description
    What went wrong → what the fix was

.EXAMPLE
    pwsh -File scripts/log-mistake.ps1 "assumed npm installed → use winget first"
#>
param(
    [Parameter(Position=0, ValueFromPipeline=$true)]
    [string]$Description
)
$ErrorActionPreference = 'Stop'

$ClaudeMd = Join-Path $PSScriptRoot '..' '.claude' 'CLAUDE.md' | Resolve-Path

if (-not $Description) {
    if (-not [System.Console]::IsInputRedirected) {
        Write-Error 'Usage: log-mistake.ps1 "what went wrong → what the fix was"'
        exit 1
    }
    $Description = $input | Out-String
}

$Description = $Description.Trim()
if (-not $Description) {
    Write-Host 'log-mistake: empty description — skipping.' -ForegroundColor Yellow
    exit 0
}

$Date  = (Get-Date -AsUTC -Format 'yyyy-MM-dd')
$Entry = "- ${Date}: ${Description}"

$content = Get-Content $ClaudeMd -Raw

if ($content -notlike "*$Entry*") {
    # Append after the last dated mistake entry line
    $updated = $content -replace '(?m)(^- \d{4}-\d{2}-\d{2}:.+)(?![\s\S]*^- \d{4}-\d{2}-\d{2}:)', "`$1`n$Entry"
    if ($updated -eq $content) {
        # No existing entries — append after ## Mistake Log header
        $updated = $content -replace '(## Mistake Log)', "`$1`n`n$Entry"
    }
    [System.IO.File]::WriteAllText($ClaudeMd, $updated, [System.Text.Encoding]::UTF8)
    Write-Host "Logged: $Entry" -ForegroundColor Green
} else {
    Write-Host 'Already logged — skipping duplicate.' -ForegroundColor Yellow
}
