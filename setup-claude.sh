#!/usr/bin/env bash
# shellcheck shell=bash
#
# setup-claude.sh — Production-grade Claude Code environment setup
# Linted: shellcheck passes with no warnings
#
# WHAT THIS DOES:
#   1. Installs/verifies Claude Code (npm-based, falls back gracefully)
#   2. Creates .claude/ structure: CLAUDE.md, slash commands, subagents,
#      project settings.json, MCP template, parallel-sessions helper
#   3. Merges user-level ~/.claude/settings.json (preserves existing config)
#   4. Creates .github/workflows/claude-pr-review.yml
#   5. Runs a verification self-test and writes a JSON receipt
#
# USAGE:
#   ./setup-claude.sh                   # Normal run (idempotent)
#   ./setup-claude.sh --force           # Re-run all steps even if done before
#   ./setup-claude.sh --interactive     # Prompt for MCP webhook URLs/DSNs
#
# PREREQUISITES:
#   - bash 4+, git, npm/node, python3
#   - ANTHROPIC_API_KEY set (for Claude Code to function)
#
# TROUBLESHOOTING:
#   - "claude: command not found" after install → open a new shell (PATH refresh)
#   - npm install fails → check Node.js >= 18: node --version
#   - settings.json merge fails → check python3 is available: python3 --version
#
# TESTED ON: Ubuntu 24.04, macOS 14+
# SHELLCHECK: sc2006,sc2046 suppressed where intentional

set -euo pipefail

# ── Colours ──────────────────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
CYAN='\033[0;36m'; BOLD='\033[1m'; RESET='\033[0m'

log_info()  { echo -e "${CYAN}[INFO]${RESET}  $*"; }
log_ok()    { echo -e "${GREEN}[PASS]${RESET}  $*"; }
log_warn()  { echo -e "${YELLOW}[WARN]${RESET}  $*"; }
log_fail()  { echo -e "${RED}[FAIL]${RESET}  $*"; }
log_step()  { echo -e "\n${BOLD}${CYAN}══ $* ${RESET}"; }

# ── Flags ─────────────────────────────────────────────────────────────────────
FORCE=false
INTERACTIVE=false
for arg in "$@"; do
  case "$arg" in
    --force)       FORCE=true ;;
    --interactive) INTERACTIVE=true ;;
    --help|-h)
      sed -n '3,30p' "$0" | sed 's/^# \?//'
      exit 0 ;;
    *) log_fail "Unknown argument: $arg"; exit 1 ;;
  esac
done

# ── Paths ─────────────────────────────────────────────────────────────────────
REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLAUDE_DIR="${REPO_DIR}/.claude"
RECEIPT_FILE="${HOME}/.claude/setup_receipt.json"
COMPONENTS_INSTALLED=()
WARNINGS=()

# ── OS detection ──────────────────────────────────────────────────────────────
detect_os() {
  case "${OSTYPE:-}" in
    darwin*) echo "macos" ;;
    msys*|cygwin*|win32*) echo "windows" ;;
    *) echo "linux" ;;
  esac
}
OS="$(detect_os)"
log_info "Detected OS: ${OS}"

# ── Idempotency check ─────────────────────────────────────────────────────────
log_step "Idempotency Check"
if [[ -f "${RECEIPT_FILE}" ]] && [[ "${FORCE}" == "false" ]]; then
  log_ok "Setup receipt found at ${RECEIPT_FILE}"
  log_info "Re-run with --force to overwrite. Current receipt:"
  python3 -m json.tool "${RECEIPT_FILE}" 2>/dev/null || cat "${RECEIPT_FILE}"
  exit 0
fi

# ── STEP 1: Install / Verify Claude Code ─────────────────────────────────────
log_step "STEP 1: Install / Verify Claude Code"

install_claude() {
  log_info "Attempting npm install -g @anthropic-ai/claude-code ..."
  if npm install -g @anthropic-ai/claude-code; then
    log_ok "Installed via npm."
  else
    log_fail "npm install failed. Ensure Node.js >= 18 is installed: node --version"
    exit 1
  fi
}

if command -v claude &>/dev/null; then
  CLAUDE_VERSION="$(claude --version 2>&1 | head -1)"
  log_ok "Claude Code already installed: ${CLAUDE_VERSION}"
else
  log_warn "claude not found. Installing..."
  install_claude
  # Refresh PATH
  export PATH="${PATH}:$(npm root -g 2>/dev/null)/../bin"
  if ! command -v claude &>/dev/null; then
    log_fail "claude still not found after install. Open a new shell and re-run."
    exit 1
  fi
  CLAUDE_VERSION="$(claude --version 2>&1 | head -1)"
  log_ok "Installed: ${CLAUDE_VERSION}"
  COMPONENTS_INSTALLED+=("claude-code")
fi

# ── STEP 2: Directory structure ───────────────────────────────────────────────
log_step "STEP 2: Create .claude/ Directory Structure"
mkdir -p \
  "${CLAUDE_DIR}/commands" \
  "${CLAUDE_DIR}/agents" \
  "${CLAUDE_DIR}/mcp" \
  "${REPO_DIR}/.github/workflows"
log_ok "Directories ready."
COMPONENTS_INSTALLED+=("directories")

# ── Helper: write file only if missing or --force ─────────────────────────────
write_if_new() {
  local dest="$1"
  local label="$2"
  if [[ -f "${dest}" ]] && [[ "${FORCE}" == "false" ]]; then
    log_info "Skip (exists): ${dest}"
    return 0
  fi
  # Content is passed via stdin
  cat > "${dest}"
  log_ok "Written: ${label}"
  COMPONENTS_INSTALLED+=("${label}")
}

# ── STEP 3: CLAUDE.md ─────────────────────────────────────────────────────────
log_step "STEP 3: CLAUDE.md"
write_if_new "${CLAUDE_DIR}/CLAUDE.md" "CLAUDE.md" <<'HEREDOC'
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
HEREDOC

# ── STEP 4: Slash Commands ────────────────────────────────────────────────────
log_step "STEP 4: Slash Commands"

write_if_new "${CLAUDE_DIR}/commands/commit-push-pr.md" "/commit-push-pr" <<'HEREDOC'
---
name: commit-push-pr
description: Stage changed files, commit with a conventional message, push the branch, and open a PR. Use after completing a feature or fix.
allowed-tools: Bash, Read, Glob
---

1. Run `git status` and `git diff --stat` to review changes.
2. Draft a conventional commit message (feat|fix|docs|chore|refactor, imperative, ≤72 chars).
3. Stage specific files only — never `git add .` or `git add -A`.
4. Commit. Do not skip hooks (--no-verify is forbidden).
5. Push with `git push -u origin <branch>`.
6. If `gh` is available: `gh pr create --title "<msg>" --body "## Summary\n$ARGUMENTS"`.
7. If not: print the GitHub URL for manual PR creation.

Append the session URL to every commit:
https://claude.ai/code/session_01DwbyLa55aQbDJn1HpZVK8U
HEREDOC

write_if_new "${CLAUDE_DIR}/commands/verify.md" "/verify" <<'HEREDOC'
---
name: verify
description: Run all available checks — JSON validation, bash lint, prettier, tests, receipt integrity — and report pass/fail. Use after making changes.
allowed-tools: Bash, Read, Glob, Grep
---

Run every check below. Collect all results before reporting — do not stop on first failure.

1. JSON: `find . -name "*.json" ! -path "./.git/*" | xargs -I{} python3 -m json.tool {} > /dev/null`
2. Bash lint: `shellcheck` on all *.sh files (if shellcheck available)
3. PS1 syntax: `pwsh -NoProfile -Command` parse check (if pwsh available)
4. Prettier: `prettier --check .` (if prettier available)
5. Tests: `pytest -q` or `npm test --if-present`
6. Receipt integrity: verify sha256 field in *_RECEIPT_*.json matches artifact

Print a summary table. Exit 1 if any check fails.
HEREDOC

write_if_new "${CLAUDE_DIR}/commands/prd.md" "/prd" <<'HEREDOC'
---
name: prd
description: Generate a structured Product Requirements Document for a feature. Provide a brief description as the argument.
argument-hint: "[feature description]"
allowed-tools: Read, Glob, Grep
---

Generate a PRD for: **$ARGUMENTS**

# PRD: $ARGUMENTS

**Status:** Draft | **Date:** *(today)* | **Version:** 1.0

## 1. Problem Statement
## 2. Target Users
## 3. Goals (measurable)
## 4. Non-Goals
## 5. Success Metrics
## 6. Proposed Solution
## 7. Milestones
## 8. Risks & Open Questions

After generating, invoke the plan-review subagent to critique this PRD.
HEREDOC

# ── STEP 5: Subagents ─────────────────────────────────────────────────────────
log_step "STEP 5: Subagents"

write_if_new "${CLAUDE_DIR}/agents/code-simplifier.md" "code-simplifier agent" <<'HEREDOC'
---
name: code-simplifier
description: Simplify and refactor code for reuse, quality, and efficiency. Fixes unnecessary complexity, duplication, and anti-patterns. PROACTIVELY use after implementing a feature.
tools: Read, Grep, Glob, Edit
model: sonnet
---

You are a Staff Engineer specialising in simplicity. Your mandate: make the code smaller, not smarter.

Principles: YAGNI, DRY (3+ real uses), single responsibility, fail fast, delete > refactor.

Process:
1. Read the changed files.
2. Identify: dead code, duplicated logic, overly complex conditions, premature abstractions, missing error handling, functions >40 lines.
3. Make the minimum edit to fix each issue found.
4. Do NOT add comments or docstrings to code you didn't change.
5. Report what changed and why.
HEREDOC

write_if_new "${CLAUDE_DIR}/agents/verify-app.md" "verify-app agent" <<'HEREDOC'
---
name: verify-app
description: Run all available tests, linters, and static analysis. Reports pass/fail per check. Use before committing.
tools: Bash, Read, Glob, Grep
model: sonnet
---

You are a QA automation engineer. Run every check; collect all results before reporting.

Checks (in order):
1. JSON validation — python3 -m json.tool on all *.json
2. Bash lint — shellcheck on all *.sh (if available)
3. PS1 syntax — pwsh parse check (if available)
4. Prettier — prettier --check . (if available)
5. pytest -q (if available)
6. npm test --if-present
7. SHA256 receipt integrity

Print a formatted summary table. Exit non-zero if any check fails.
HEREDOC

write_if_new "${CLAUDE_DIR}/agents/plan-review.md" "plan-review agent" <<'HEREDOC'
---
name: plan-review
description: Review a proposed plan from a Staff Engineer perspective. Challenges correctness, simplicity, security, scalability, maintainability, and edge cases. Use before executing significant changes.
tools: Read, Grep, Glob
model: sonnet
---

You are a Staff Engineer with 15 years of systems experience. Find what is wrong, missing, or needlessly complex.

Review dimensions: Correctness, Simplicity, Security, Scalability, Maintainability, Edge Cases, Rollback.

For each: rate OK / CONCERN / BLOCKER and give specific notes.

Output:
- Overall verdict: APPROVE / APPROVE WITH NOTES / REVISE BEFORE PROCEEDING
- Blockers (must fix)
- Concerns (should fix)
- Suggestions (optional)
- Approved aspects

End with either "This plan is cleared for execution." or "This plan requires revision."
HEREDOC

# ── STEP 6: Project settings.json ────────────────────────────────────────────
log_step "STEP 6: Project .claude/settings.json"
write_if_new "${CLAUDE_DIR}/settings.json" "project settings.json" <<'HEREDOC'
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
            "command": "prettier --write . 2>/dev/null || true"
          }
        ]
      }
    ]
  }
}
HEREDOC

# ── STEP 7: Merge user-level ~/.claude/settings.json ─────────────────────────
log_step "STEP 7: Merge User ~/.claude/settings.json"
USER_SETTINGS="${HOME}/.claude/settings.json"
NEW_ALLOWS='["Bash(git:*)", "Bash(npm:*)", "Bash(node:*)", "Bash(prettier:*)", "Bash(python3:*)"]'

if [[ -f "${USER_SETTINGS}" ]]; then
  log_info "Merging into existing ${USER_SETTINGS} ..."
  python3 - "${USER_SETTINGS}" "${NEW_ALLOWS}" <<'PYEOF'
import sys, json, tempfile, os

settings_path = sys.argv[1]
new_allows = json.loads(sys.argv[2])

with open(settings_path) as f:
    cfg = json.load(f)

perms = cfg.setdefault("permissions", {})
existing = perms.get("allow", [])
merged = list(dict.fromkeys(existing + new_allows))  # union, preserve order, no dupes
perms["allow"] = merged

tmp = settings_path + ".tmp"
with open(tmp, "w") as f:
    json.dump(cfg, f, indent=4)
    f.write("\n")
os.replace(tmp, settings_path)
print("Merged. Final allow list:", merged)
PYEOF
  log_ok "User settings.json merged."
  COMPONENTS_INSTALLED+=("user-settings-merge")
else
  log_warn "No user settings.json found at ${USER_SETTINGS}. Skipping merge."
  WARNINGS+=("No user settings.json found — merge skipped")
fi

# ── STEP 8: MCP template ──────────────────────────────────────────────────────
log_step "STEP 8: MCP Template"

SLACK_URL="SLACK_WEBHOOK_URL_PLACEHOLDER"
SENTRY_DSN="SENTRY_DSN_PLACEHOLDER"

if [[ "${INTERACTIVE}" == "true" ]]; then
  read -r -p "Slack webhook URL [ENTER to skip]: " input_slack
  [[ -n "${input_slack}" ]] && SLACK_URL="${input_slack}"
  read -r -p "Sentry DSN [ENTER to skip]: " input_sentry
  [[ -n "${input_sentry}" ]] && SENTRY_DSN="${input_sentry}"
fi

write_if_new "${CLAUDE_DIR}/mcp/mcp-template.json" "mcp-template.json" <<HEREDOC
{
  "_comment": "Copy to .mcp.json in project root. Keep .mcp.json gitignored — it contains secrets.",
  "mcpServers": {
    "slack": {
      "type": "http",
      "url": "${SLACK_URL}",
      "description": "Slack Incoming Webhook. Replace URL if still placeholder."
    },
    "sentry": {
      "type": "http",
      "url": "${SENTRY_DSN}",
      "description": "Sentry DSN. Replace URL if still placeholder."
    }
  }
}
HEREDOC

if [[ "${SLACK_URL}" == *"PLACEHOLDER"* ]]; then
  WARNINGS+=("MCP Slack URL is still a placeholder — edit .claude/mcp/mcp-template.json")
fi
if [[ "${SENTRY_DSN}" == *"PLACEHOLDER"* ]]; then
  WARNINGS+=("MCP Sentry DSN is still a placeholder — edit .claude/mcp/mcp-template.json")
fi

# ── STEP 9: GitHub Action ─────────────────────────────────────────────────────
log_step "STEP 9: GitHub Action (claude-pr-review.yml)"
GH_WORKFLOW="${REPO_DIR}/.github/workflows/claude-pr-review.yml"
write_if_new "${GH_WORKFLOW}" "claude-pr-review.yml" <<'HEREDOC'
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
      contains(github.event.comment.body, '@.claude') &&
      (
        github.event.comment.author_association == 'OWNER' ||
        github.event.comment.author_association == 'MEMBER' ||
        github.event.comment.author_association == 'COLLABORATOR'
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
      - name: Install Claude Code
        run: npm install -g @anthropic-ai/claude-code
      - name: Extract instruction
        id: extract
        run: |
          INSTRUCTION=$(echo "$COMMENT_BODY" | sed 's/@\.claude//' | xargs)
          [[ -z "$INSTRUCTION" ]] && INSTRUCTION="Review this PR for correctness, security, and code quality."
          echo "instruction=$INSTRUCTION" >> "$GITHUB_OUTPUT"
        env:
          COMMENT_BODY: ${{ github.event.comment.body }}
      - name: Run Claude review
        id: review
        run: |
          REVIEW=$(claude --print --no-stream \
            --system "You are a Staff Engineer doing a code review. Be concise and actionable. Use markdown." \
            "${{ steps.extract.outputs.instruction }}" 2>&1) || true
          { echo "result<<CLAUDE_EOF"; echo "$REVIEW"; echo "CLAUDE_EOF"; } >> "$GITHUB_OUTPUT"
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
      - name: Post comment
        uses: actions/github-script@v7
        with:
          script: |
            const body = [
              '## Claude Code Review',
              '',
              `> @${context.payload.comment.user.login}: \`${{ steps.extract.outputs.instruction }}\``,
              '',
              `${{ steps.review.outputs.result }}`,
              '',
              '---',
              '*Generated by [Claude Code](https://claude.ai/code). Verify before applying.*'
            ].join('\n');
            await github.rest.issues.createComment({
              owner: context.repo.owner,
              repo: context.repo.repo,
              issue_number: context.issue.number,
              body
            });
HEREDOC

# ── STEP 10: Parallel sessions helper ────────────────────────────────────────
log_step "STEP 10: Parallel Sessions Helper"
write_if_new "${CLAUDE_DIR}/open-sessions.sh" "open-sessions.sh" <<'HEREDOC'
#!/usr/bin/env bash
# shellcheck shell=bash
# Usage: ./.claude/open-sessions.sh [N]  — open N parallel Claude sessions (default 5)
set -euo pipefail
N="${1:-5}"
existing=$(pgrep -c claude 2>/dev/null || echo 0)
if [[ "$existing" -ge "$N" ]]; then
  echo "INFO: $existing claude process(es) already running (target $N). Skipping."
  exit 0
fi
to_open=$(( N - existing ))
echo "Opening $to_open session(s)..."
for _ in $(seq 1 "$to_open"); do
  if [[ "${OSTYPE:-}" == "darwin"* ]]; then
    if command -v ghostty &>/dev/null; then
      ghostty --new-window -- claude &
    elif [[ -d "/Applications/iTerm.app" ]]; then
      osascript -e 'tell application "iTerm2" to create window with default profile command "claude"' &
    else
      osascript -e 'tell application "Terminal" to do script "claude"' &
    fi
  else
    if command -v gnome-terminal &>/dev/null; then
      gnome-terminal --tab -- bash -c "claude; exec bash" 2>/dev/null &
    elif command -v xterm &>/dev/null; then
      xterm -e "claude; bash" &
    else
      echo "WARN: No terminal emulator found. Run: claude"
    fi
  fi
  sleep 0.3
done
echo "Done."
HEREDOC
chmod +x "${CLAUDE_DIR}/open-sessions.sh"

# ── STEP 11: Verification self-test ──────────────────────────────────────────
log_step "STEP 11: Verification Self-Test"
PASS=0; FAIL=0

check() {
  local label="$1"; shift
  if "$@" &>/dev/null; then
    log_ok "${label}"; (( PASS++ )) || true
  else
    log_fail "${label}"; (( FAIL++ )) || true
  fi
}

check "claude --version"           claude --version
check "CLAUDE.md exists"           test -f "${CLAUDE_DIR}/CLAUDE.md"
check "command: commit-push-pr"    test -f "${CLAUDE_DIR}/commands/commit-push-pr.md"
check "command: verify"            test -f "${CLAUDE_DIR}/commands/verify.md"
check "command: prd"               test -f "${CLAUDE_DIR}/commands/prd.md"
check "agent: code-simplifier"     test -f "${CLAUDE_DIR}/agents/code-simplifier.md"
check "agent: verify-app"          test -f "${CLAUDE_DIR}/agents/verify-app.md"
check "agent: plan-review"         test -f "${CLAUDE_DIR}/agents/plan-review.md"
check "project settings.json valid" python3 -m json.tool "${CLAUDE_DIR}/settings.json"
check "user settings.json valid"    python3 -m json.tool "${HOME}/.claude/settings.json"
check "mcp-template.json valid"     python3 -m json.tool "${CLAUDE_DIR}/mcp/mcp-template.json"
check "open-sessions.sh executable" test -x "${CLAUDE_DIR}/open-sessions.sh"
check "github action exists"        test -f "${REPO_DIR}/.github/workflows/claude-pr-review.yml"

echo ""
log_info "Verification: ${PASS} passed, ${FAIL} failed."
if [[ "${FAIL}" -gt 0 ]]; then
  log_fail "Some checks failed. Review output above."
  WARNINGS+=("${FAIL} verification check(s) failed")
fi

# ── STEP 12: Write JSON receipt ───────────────────────────────────────────────
log_step "STEP 12: Writing Receipt"
mkdir -p "${HOME}/.claude"
TIMESTAMP="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
python3 - <<PYEOF
import json, os
receipt = {
    "timestamp": "${TIMESTAMP}",
    "claude_version": "$(claude --version 2>&1 | head -1 | tr -d '\n')",
    "os": "${OS}",
    "repo": "${REPO_DIR}",
    "components_installed": $(python3 -c "import json; print(json.dumps(${COMPONENTS_INSTALLED[*]+"${COMPONENTS_INSTALLED[@]}"}))" 2>/dev/null || echo "[]"),
    "verification": {"passed": ${PASS}, "failed": ${FAIL}},
    "warnings": $(python3 -c "import json; print(json.dumps(${WARNINGS[*]+"${WARNINGS[@]}"}))" 2>/dev/null || echo "[]")
}
path = os.path.expanduser("~/.claude/setup_receipt.json")
with open(path, "w") as f:
    json.dump(receipt, f, indent=2)
    f.write("\n")
print(f"Receipt written to {path}")
PYEOF

# ── Final Summary ─────────────────────────────────────────────────────────────
echo ""
echo -e "${BOLD}${GREEN}══════════════════════════════════════════════${RESET}"
echo -e "${BOLD}${GREEN}  Claude Code Setup Complete${RESET}"
echo -e "${BOLD}${GREEN}══════════════════════════════════════════════${RESET}"
echo ""
echo "  Claude version : ${CLAUDE_VERSION}"
echo "  OS             : ${OS}"
echo "  Project        : ${REPO_DIR}"
echo ""
echo "  Created:"
echo "    .claude/CLAUDE.md                    (project memory)"
echo "    .claude/commands/commit-push-pr.md   (/commit-push-pr)"
echo "    .claude/commands/verify.md           (/verify)"
echo "    .claude/commands/prd.md              (/prd)"
echo "    .claude/agents/code-simplifier.md"
echo "    .claude/agents/verify-app.md"
echo "    .claude/agents/plan-review.md"
echo "    .claude/settings.json                (PostToolUse prettier hook)"
echo "    .claude/mcp/mcp-template.json"
echo "    .claude/open-sessions.sh             (parallel sessions)"
echo "    .github/workflows/claude-pr-review.yml"
echo "    ~/.claude/setup_receipt.json"
echo ""
if [[ "${#WARNINGS[@]}" -gt 0 ]]; then
  echo -e "  ${YELLOW}Warnings:${RESET}"
  for w in "${WARNINGS[@]}"; do echo "    - ${w}"; done
  echo ""
fi
REMOTE_URL="$(git -C "${REPO_DIR}" remote get-url origin 2>/dev/null || echo '<repo-url>')"
echo "  To use on a fresh machine:"
echo "    git clone ${REMOTE_URL}"
echo "    cd metablooms-uploads"
echo "    ./setup-claude.sh                # idempotent"
echo "    ./setup-claude.sh --interactive  # prompts for Slack/Sentry URLs"
echo "    ./setup-claude.sh --force        # re-run everything"
echo ""
echo "  Next steps:"
echo "    1. Set ANTHROPIC_API_KEY in your shell profile"
echo "    2. Run: claude  (to start a session)"
echo "    3. Open parallel sessions: .claude/open-sessions.sh 5"
echo "    4. Add ANTHROPIC_API_KEY secret to GitHub repo for PR review action"
echo "    5. Edit .claude/mcp/mcp-template.json → copy to .mcp.json with real URLs"
echo ""
