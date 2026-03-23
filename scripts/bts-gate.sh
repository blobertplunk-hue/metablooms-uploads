#!/usr/bin/env bash
# scripts/bts-gate.sh — PreToolUse hard-block gate
#
# Blocks any tool use (except BTS-recording calls) when the current session
# has zero decisions recorded.  Exits 0 (allow) or 2 (block).
#
# Claude Code PreToolUse hook exit codes:
#   0  → allow
#   1  → warn but allow
#   2  → block with the message on stdout
#
# Called by the PreToolUse hook in settings.json.
# Environment variables provided by Claude Code:
#   CLAUDE_TOOL_NAME        e.g. "Bash"
#   CLAUDE_TOOL_INPUT       JSON string of the tool call arguments
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CURRENT_FILE="${REPO_DIR}/_bts/.current"

TOOL_NAME="${CLAUDE_TOOL_NAME:-}"
TOOL_INPUT="${CLAUDE_TOOL_INPUT:-}"

# ── Pass-through: BTS recording calls are always allowed ─────────────────────
# Allow bts-record.sh, bts-init.sh, bts-finalize.sh, /bts command, log-mistake
if echo "${TOOL_INPUT}" | grep -qE "bts-record|bts-init|bts-finalize|bts-gate|log-mistake|scripts/bts" 2>/dev/null; then
  exit 0
fi

# ── No session file means hooks aren't set up yet — soft warn ────────────────
if [[ ! -f "${CURRENT_FILE}" ]]; then
  exit 0
fi

SESSION_FILE="$(cat "${CURRENT_FILE}" 2>/dev/null || echo '')"
if [[ -z "${SESSION_FILE}" || ! -f "${SESSION_FILE}" ]]; then
  exit 0
fi

# ── Count decisions ──────────────────────────────────────────────────────────
DECISION_COUNT="$(python3 - "${SESSION_FILE}" <<'PYEOF'
import json, sys
try:
    with open(sys.argv[1]) as f:
        d = json.load(f)
    print(len(d.get("decisions", [])))
except Exception:
    print(0)
PYEOF
)"

if [[ "${DECISION_COUNT}" == "0" ]]; then
  echo "BTS GATE BLOCKED: Zero decisions recorded for this session."
  echo "Record BTS decisions with: bash scripts/bts-record.sh '{}'"
  echo "Or use the /bts skill to batch-record all decisions."
  echo "This is mandatory per CLAUDE.md Layer 0."
  exit 2
fi

exit 0
