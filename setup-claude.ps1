#Requires -Version 7.0
<#
.SYNOPSIS
    Production-grade Claude Code environment setup for Windows (PowerShell 7).

.DESCRIPTION
    PowerShell equivalent of setup-claude.sh. Creates .claude/ structure,
    installs Claude Code, merges user settings, and writes a JSON receipt.

.PARAMETER Force
    Re-run all steps even if setup was already completed.

.PARAMETER Interactive
    Prompt for MCP webhook URLs/DSNs instead of using placeholders.

.EXAMPLE
    pwsh -File setup-claude.ps1
    pwsh -File setup-claude.ps1 -Force
    pwsh -File setup-claude.ps1 -Interactive

.NOTES
    Prerequisites: Node.js >= 18, git, python3 (or python)
    Set ANTHROPIC_API_KEY in your environment for Claude Code to function.
#>
[CmdletBinding()]
param(
    [switch]$Force,
    [switch]$Interactive
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

# ── Colours ───────────────────────────────────────────────────────────────────
function Write-Info  { param($m) Write-Host "[INFO]  $m" -ForegroundColor Cyan }
function Write-Ok    { param($m) Write-Host "[PASS]  $m" -ForegroundColor Green }
function Write-Warn  { param($m) Write-Host "[WARN]  $m" -ForegroundColor Yellow }
function Write-Fail  { param($m) Write-Host "[FAIL]  $m" -ForegroundColor Red }
function Write-Step  { param($m) Write-Host "`n== $m ==" -ForegroundColor Cyan }

# ── Paths ─────────────────────────────────────────────────────────────────────
$RepoDir     = $PSScriptRoot
$ClaudeDir   = Join-Path $RepoDir '.claude'
$HomeDir     = $HOME
$ClaudeHome  = Join-Path $HomeDir '.claude'
$ReceiptFile = Join-Path $ClaudeHome 'setup_receipt.json'

$ComponentsInstalled = [System.Collections.Generic.List[string]]::new()
$Warnings            = [System.Collections.Generic.List[string]]::new()

# ── Python binary (python3 or python) ────────────────────────────────────────
$Python = $null
foreach ($py in @('python3','python')) {
    if (Get-Command $py -ErrorAction SilentlyContinue) { $Python = $py; break }
}
if (-not $Python) {
    Write-Fail 'python3/python not found. Install Python 3 and add to PATH.'
    exit 1
}

# ── Idempotency ───────────────────────────────────────────────────────────────
Write-Step 'Idempotency Check'
if ((Test-Path $ReceiptFile) -and -not $Force) {
    Write-Ok "Setup receipt found at $ReceiptFile"
    Write-Info 'Re-run with -Force to overwrite. Current receipt:'
    Get-Content $ReceiptFile | & $Python -m json.tool
    exit 0
}

# ── STEP 1: Install / verify Claude Code ─────────────────────────────────────
Write-Step 'STEP 1: Install / Verify Claude Code'

function Install-ClaudeCode {
    Write-Info 'Running: npm install -g @anthropic-ai/claude-code'
    npm install -g @anthropic-ai/claude-code
    if ($LASTEXITCODE -ne 0) {
        Write-Fail 'npm install failed. Ensure Node.js >= 18: node --version'
        exit 1
    }
}

$ClaudeVersion = $null
$claudeCmd = Get-Command 'claude' -ErrorAction SilentlyContinue
if ($claudeCmd) {
    $ClaudeVersion = (& claude --version 2>&1 | Select-Object -First 1).ToString().Trim()
    Write-Ok "Claude Code already installed: $ClaudeVersion"
} else {
    Write-Warn 'claude not found. Installing...'
    Install-ClaudeCode
    $claudeCmd = Get-Command 'claude' -ErrorAction SilentlyContinue
    if (-not $claudeCmd) {
        Write-Fail 'claude still not found after install. Open a new shell and re-run.'
        exit 1
    }
    $ClaudeVersion = (& claude --version 2>&1 | Select-Object -First 1).ToString().Trim()
    Write-Ok "Installed: $ClaudeVersion"
    $null = $ComponentsInstalled.Add('claude-code')
}

# ── STEP 2: Directory structure ───────────────────────────────────────────────
Write-Step 'STEP 2: Create .claude/ Directory Structure'
foreach ($d in @(
    (Join-Path $ClaudeDir 'commands'),
    (Join-Path $ClaudeDir 'agents'),
    (Join-Path $ClaudeDir 'mcp'),
    (Join-Path $RepoDir '.github' 'workflows'),
    $ClaudeHome
)) {
    New-Item -ItemType Directory -Path $d -Force | Out-Null
}
Write-Ok 'Directories ready.'
$null = $ComponentsInstalled.Add('directories')

# ── Helper: write file only if missing or -Force ──────────────────────────────
function Write-IfNew {
    param([string]$Path, [string]$Label, [string]$Content)
    if ((Test-Path $Path) -and -not $Force) {
        Write-Info "Skip (exists): $Path"
        return
    }
    [System.IO.File]::WriteAllText($Path, $Content, [System.Text.Encoding]::UTF8)
    Write-Ok "Written: $Label"
    $null = $ComponentsInstalled.Add($Label)
}

# ── STEP 3: CLAUDE.md ─────────────────────────────────────────────────────────
Write-Step 'STEP 3: CLAUDE.md'
Write-IfNew (Join-Path $ClaudeDir 'CLAUDE.md') 'CLAUDE.md' @'
# Project Memory

## Boris Cherny Core Rules
- Run parallel agents for independent subtasks; never serialize what can be parallelized.
- Use plan mode first. Only switch to auto-accept for well-scoped execution.
- Run a verification loop after every change: tests must pass before committing.
- When you make a mistake, update this file so you don't repeat it.
- Fail-closed: never silently continue on error.

## Aakash Gupta — PRD Writer
Use /prd to generate a structured PRD: problem, users, goals, non-goals, success metrics, milestones.

## Jacob Bartlett — Staff Engineer Review
Before finalizing any plan, spawn the plan-review subagent to critique the approach:
scalability, security, maintainability, edge cases, simpler alternatives.

## Mistake Log
<!-- Claude: append entries here when an error is corrected.
     Format: YYYY-MM-DD: [what went wrong] → [fix applied] -->
'@

# ── STEP 4: Slash commands ────────────────────────────────────────────────────
Write-Step 'STEP 4: Slash Commands'
Write-IfNew (Join-Path $ClaudeDir 'commands' 'commit-push-pr.md') '/commit-push-pr' @'
---
name: commit-push-pr
description: Stage changed files, commit with a conventional message, push the branch, and open a PR.
allowed-tools: Bash, Read, Glob
---

1. Run `git status` and `git diff --stat` to review changes.
2. Draft a conventional commit message (feat|fix|docs|chore|refactor, <=72 chars).
3. Stage specific files only — never `git add .` or `git add -A`.
4. Commit. Do not skip hooks (--no-verify is forbidden).
5. Push with `git push -u origin <branch>`.
6. If `gh` is available: `gh pr create --title "<msg>" --body "## Summary\n$ARGUMENTS"`.
'@

Write-IfNew (Join-Path $ClaudeDir 'commands' 'verify.md') '/verify' @'
---
name: verify
description: Run all available checks and report pass/fail.
allowed-tools: Bash, Read, Glob, Grep
---

Run every check below. Collect all results before reporting.

1. JSON: validate all *.json with python3 -m json.tool
2. Bash lint: shellcheck on all *.sh (if available)
3. Prettier: prettier --check . (if available)
4. Tests: pytest -q or npm test --if-present
5. Receipt integrity: verify sha256 in *_RECEIPT_*.json

Print a summary table. Exit 1 if any check fails.
'@

Write-IfNew (Join-Path $ClaudeDir 'commands' 'prd.md') '/prd' @'
---
name: prd
description: Generate a structured PRD for a feature.
argument-hint: "[feature description]"
allowed-tools: Read, Glob, Grep
---

Generate a PRD for: **$ARGUMENTS**

# PRD: $ARGUMENTS

**Status:** Draft | **Version:** 1.0

## 1. Problem Statement
## 2. Target Users
## 3. Goals (measurable)
## 4. Non-Goals
## 5. Success Metrics
## 6. Proposed Solution
## 7. Milestones
## 8. Risks & Open Questions
'@

# ── STEP 5: Subagents ─────────────────────────────────────────────────────────
Write-Step 'STEP 5: Subagents'
Write-IfNew (Join-Path $ClaudeDir 'agents' 'code-simplifier.md') 'code-simplifier' @'
---
name: code-simplifier
description: Simplify and refactor code for reuse, quality, and efficiency.
tools: Read, Grep, Glob, Edit
model: sonnet
---

You are a Staff Engineer specialising in simplicity.
Principles: YAGNI, DRY, single responsibility, fail fast, delete > refactor.
Report what changed and why. Do not add comments to unchanged code.
'@

Write-IfNew (Join-Path $ClaudeDir 'agents' 'verify-app.md') 'verify-app' @'
---
name: verify-app
description: Run all tests, linters, and static analysis. Report pass/fail.
tools: Bash, Read, Glob, Grep
model: sonnet
---

Run every check; collect all results before reporting.
Checks: JSON, shellcheck, prettier, pytest, npm test, receipt SHA256.
Print a formatted summary table. Exit non-zero if any check fails.
'@

Write-IfNew (Join-Path $ClaudeDir 'agents' 'plan-review.md') 'plan-review' @'
---
name: plan-review
description: Review a plan from a Staff Engineer perspective before execution.
tools: Read, Grep, Glob
model: sonnet
---

Review dimensions: Correctness, Simplicity, Security, Scalability, Maintainability, Edge Cases, Rollback.
Rate each: OK / CONCERN / BLOCKER.
Verdict: APPROVE / APPROVE WITH NOTES / REVISE BEFORE PROCEEDING.
'@

# ── STEP 6: Project settings.json ────────────────────────────────────────────
Write-Step 'STEP 6: Project .claude/settings.json'
Write-IfNew (Join-Path $ClaudeDir 'settings.json') 'project settings.json' @'
{
  "$schema": "https://json.schemastore.org/claude-code-settings.json",
  "permissions": {
    "allow": [
      "Bash(git:*)",
      "Bash(npm:*)",
      "Bash(node:*)",
      "Bash(prettier:*)",
      "Bash(python3:*)",
      "Bash(sha256sum:*)",
      "Bash(shellcheck:*)"
    ]
  },
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "prettier --write . 2>$null; exit 0"
          }
        ]
      }
    ]
  }
}
'@

# ── STEP 7: Merge user ~/.claude/settings.json ────────────────────────────────
Write-Step 'STEP 7: Merge User ~/.claude/settings.json'
$UserSettings = Join-Path $ClaudeHome 'settings.json'
$NewAllows = @('Bash(git:*)','Bash(npm:*)','Bash(node:*)','Bash(prettier:*)','Bash(python3:*)')

if (Test-Path $UserSettings) {
    Write-Info "Merging into $UserSettings ..."
    $cfg = Get-Content $UserSettings -Raw | ConvertFrom-Json -AsHashtable
    if (-not $cfg.ContainsKey('permissions')) { $cfg['permissions'] = @{} }
    $perms = $cfg['permissions']
    if (-not $perms.ContainsKey('allow')) { $perms['allow'] = @() }
    $merged = ($perms['allow'] + $NewAllows) | Sort-Object -Unique
    $perms['allow'] = $merged
    $cfg | ConvertTo-Json -Depth 10 | Set-Content $UserSettings -Encoding UTF8
    Write-Ok 'User settings.json merged.'
    $null = $ComponentsInstalled.Add('user-settings-merge')
} else {
    Write-Warn "No user settings.json at $UserSettings — skipping merge."
    $null = $Warnings.Add("No user settings.json found — merge skipped")
}

# ── STEP 8: MCP template ──────────────────────────────────────────────────────
Write-Step 'STEP 8: MCP Template'
$SlackUrl  = 'SLACK_WEBHOOK_URL_PLACEHOLDER'
$SentryDsn = 'SENTRY_DSN_PLACEHOLDER'

if ($Interactive) {
    $input = Read-Host 'Slack webhook URL [ENTER to skip]'
    if ($input) { $SlackUrl = $input }
    $input = Read-Host 'Sentry DSN [ENTER to skip]'
    if ($input) { $SentryDsn = $input }
}

Write-IfNew (Join-Path $ClaudeDir 'mcp' 'mcp-template.json') 'mcp-template.json' @"
{
  "_comment": "Copy to .mcp.json in project root. Keep .mcp.json gitignored.",
  "mcpServers": {
    "slack": {
      "type": "http",
      "url": "$SlackUrl"
    },
    "sentry": {
      "type": "http",
      "url": "$SentryDsn"
    }
  }
}
"@

if ($SlackUrl -like '*PLACEHOLDER*')  { $null = $Warnings.Add('MCP Slack URL is still a placeholder') }
if ($SentryDsn -like '*PLACEHOLDER*') { $null = $Warnings.Add('MCP Sentry DSN is still a placeholder') }

# ── STEP 9: GitHub Action ─────────────────────────────────────────────────────
Write-Step 'STEP 9: GitHub Action'
Write-IfNew (Join-Path $RepoDir '.github' 'workflows' 'claude-pr-review.yml') 'claude-pr-review.yml' @'
name: Claude PR Review
on:
  issue_comment:
    types: [created]
permissions:
  contents: read
  issues: write
  pull-requests: write
jobs:
  claude-review:
    if: |
      contains(github.event.comment.body, "@.claude") &&
      (
        github.event.comment.author_association == "OWNER" ||
        github.event.comment.author_association == "MEMBER" ||
        github.event.comment.author_association == "COLLABORATOR"
      )
    runs-on: ubuntu-latest
    timeout-minutes: 15
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - uses: actions/setup-node@v4
        with:
          node-version: "22"
      - run: npm install -g @anthropic-ai/claude-code
      - name: Run Claude review
        id: review
        run: |
          REVIEW=$(claude --print --no-stream "${{ github.event.comment.body }}" 2>&1) || true
          { echo "result<<CLAUDE_EOF"; echo "$REVIEW"; echo "CLAUDE_EOF"; } >> "$GITHUB_OUTPUT"
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
      - uses: actions/github-script@v7
        with:
          script: |
            await github.rest.issues.createComment({
              owner: context.repo.owner, repo: context.repo.repo,
              issue_number: context.issue.number,
              body: "## Claude Review\n\n${{ steps.review.outputs.result }}"
            });
'@

# ── STEP 10: Verification ─────────────────────────────────────────────────────
Write-Step 'STEP 10: Verification Self-Test'
$Pass = 0; $Fail = 0

function Test-Check {
    param([string]$Label, [scriptblock]$Block)
    try {
        & $Block | Out-Null
        Write-Ok $Label; $script:Pass++
    } catch {
        Write-Fail $Label; $script:Fail++
    }
}

Test-Check 'claude --version'           { claude --version }
Test-Check 'CLAUDE.md exists'           { if (-not (Test-Path (Join-Path $ClaudeDir 'CLAUDE.md'))) { throw } }
Test-Check 'command: commit-push-pr'    { if (-not (Test-Path (Join-Path $ClaudeDir 'commands' 'commit-push-pr.md'))) { throw } }
Test-Check 'command: verify'            { if (-not (Test-Path (Join-Path $ClaudeDir 'commands' 'verify.md'))) { throw } }
Test-Check 'command: prd'               { if (-not (Test-Path (Join-Path $ClaudeDir 'commands' 'prd.md'))) { throw } }
Test-Check 'agent: code-simplifier'     { if (-not (Test-Path (Join-Path $ClaudeDir 'agents' 'code-simplifier.md'))) { throw } }
Test-Check 'agent: verify-app'          { if (-not (Test-Path (Join-Path $ClaudeDir 'agents' 'verify-app.md'))) { throw } }
Test-Check 'agent: plan-review'         { if (-not (Test-Path (Join-Path $ClaudeDir 'agents' 'plan-review.md'))) { throw } }
Test-Check 'project settings.json valid' {
    Get-Content (Join-Path $ClaudeDir 'settings.json') -Raw | & $Python -m json.tool | Out-Null
}
Test-Check 'mcp-template.json valid' {
    Get-Content (Join-Path $ClaudeDir 'mcp' 'mcp-template.json') -Raw | & $Python -m json.tool | Out-Null
}
Test-Check 'github action exists' { if (-not (Test-Path (Join-Path $RepoDir '.github' 'workflows' 'claude-pr-review.yml'))) { throw } }

Write-Info "Verification: $Pass passed, $Fail failed."

# ── STEP 11: Write receipt ────────────────────────────────────────────────────
Write-Step 'STEP 11: Writing Receipt'
$receipt = [ordered]@{
    timestamp            = (Get-Date -Format 'yyyy-MM-ddTHH:mm:ssZ' -AsUTC)
    claude_version       = $ClaudeVersion
    os                   = 'windows'
    repo                 = $RepoDir
    components_installed = $ComponentsInstalled.ToArray()
    verification         = [ordered]@{ passed = $Pass; failed = $Fail }
    warnings             = $Warnings.ToArray()
}
$receipt | ConvertTo-Json -Depth 5 | Set-Content $ReceiptFile -Encoding UTF8
Write-Ok "Receipt written to $ReceiptFile"

# ── Summary ───────────────────────────────────────────────────────────────────
Write-Host ''
Write-Host '══════════════════════════════════════════════' -ForegroundColor Green
Write-Host '  Claude Code Setup Complete' -ForegroundColor Green
Write-Host '══════════════════════════════════════════════' -ForegroundColor Green
Write-Host ''
Write-Host "  Claude version : $ClaudeVersion"
Write-Host "  Repo           : $RepoDir"
Write-Host ''
Write-Host '  Created:'
Write-Host '    .claude/CLAUDE.md'
Write-Host '    .claude/commands/  (commit-push-pr, verify, prd)'
Write-Host '    .claude/agents/    (code-simplifier, verify-app, plan-review)'
Write-Host '    .claude/settings.json'
Write-Host '    .claude/mcp/mcp-template.json'
Write-Host '    .github/workflows/claude-pr-review.yml'
Write-Host "    $ReceiptFile"
Write-Host ''

if ($Warnings.Count -gt 0) {
    Write-Host '  Warnings:' -ForegroundColor Yellow
    foreach ($w in $Warnings) { Write-Host "    - $w" -ForegroundColor Yellow }
    Write-Host ''
}

Write-Host '  Next steps:'
Write-Host '    1. Set $env:ANTHROPIC_API_KEY in your PowerShell profile'
Write-Host '    2. Run: claude'
Write-Host '    3. Add ANTHROPIC_API_KEY secret to GitHub for PR review action'
Write-Host '    4. Edit .claude/mcp/mcp-template.json -> copy to .mcp.json with real URLs'
Write-Host ''

if ($Fail -gt 0) { exit 1 }
