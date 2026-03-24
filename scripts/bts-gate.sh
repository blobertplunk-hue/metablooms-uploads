#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BTS_DIR="${REPO_DIR}/_bts"
CURRENT_FILE="${BTS_DIR}/.current"
BYPASS_FILE="${BTS_DIR}/.bypass"
TOOL_NAME="${CLAUDE_TOOL_NAME:-}"
TOOL_INPUT="${CLAUDE_TOOL_INPUT:-}"

# ─── MANUAL ESCAPE ────────────────────────────────────────────────────────────
# If locked out, use ONE of:
#   touch _bts/.bypass          (persistent until you rm it)
#   BTS_BYPASS=1 <command>      (one-shot env var)
# ─────────────────────────────────────────────────────────────────────────────
if [[ "${BTS_BYPASS:-}" == "1" ]] || [[ -f "${BYPASS_FILE}" ]]; then
  exit 0
fi

# ─── ALWAYS-ALLOW PASSTHROUGHS ───────────────────────────────────────────────
# BTS and self-repair paths
if printf '%s' "${TOOL_INPUT}" | grep -qF 'bts'; then exit 0; fi
if printf '%s' "${TOOL_INPUT}" | grep -qF 'log-mistake'; then exit 0; fi

# Read-safe tools (never block exploration or BTS writes)
case "${TOOL_NAME}" in
  Read|Glob|Grep|WebFetch|WebSearch|Write) exit 0 ;;
esac

# Git operations
if printf '%s' "${TOOL_INPUT}" | grep -qE '"git '; then exit 0; fi

# ─── MANDATORY GATE ──────────────────────────────────────────────────────────

_blocked() {
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo "BTS GATE BLOCKED: $1"
  echo ""
  echo "FIX:    bash scripts/bts-init.sh    (start a session)"
  echo "        bash scripts/bts-record.sh '{...}'  (record a decision)"
  echo ""
  echo "ESCAPE: touch _bts/.bypass          (persistent bypass)"
  echo "        BTS_BYPASS=1 <command>      (one-shot bypass)"
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  exit 2
}

# No session initialized
if [[ ! -f "${CURRENT_FILE}" ]]; then
  _blocked "no active BTS session. Run: bash scripts/bts-init.sh"
fi

SESSION_FILE="$(cat "${CURRENT_FILE}" 2>/dev/null || true)"
if [[ -z "${SESSION_FILE}" || ! -f "${SESSION_FILE}" ]]; then
  _blocked "session pointer is missing or corrupt. Run: bash scripts/bts-init.sh"
fi

# Count decisions — never let parse failure crash the gate
COUNT=$(python3 -c "
import json, sys
try:
    d = json.load(open(sys.argv[1], 'r', encoding='utf-8'))
    print(len(d.get('decisions', [])))
except Exception:
    print(0)
" "${SESSION_FILE}" 2>/dev/null || printf '0')

if [[ "${COUNT}" == "0" ]]; then
  _blocked "0 decisions recorded this session. Record one: bash scripts/bts-record.sh '{...}'"
fi

exit 0
