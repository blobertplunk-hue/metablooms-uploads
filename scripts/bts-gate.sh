#!/usr/bin/env bash

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CURRENT_FILE="${REPO_DIR}/_bts/.current"
TOOL_NAME="${CLAUDE_TOOL_NAME:-}"
TOOL_INPUT="${CLAUDE_TOOL_INPUT:-}"

# BTS emergency bypass
if [[ "${BTS_BYPASS:-}" == "1" ]]; then exit 0; fi

# Always allow BTS and self-repair paths
if printf '%s' "${TOOL_INPUT}" | grep -qF 'bts'; then exit 0; fi
if printf '%s' "${TOOL_INPUT}" | grep -qF 'bts-gate'; then exit 0; fi
if printf '%s' "${TOOL_INPUT}" | grep -qF 'log-mistake'; then exit 0; fi

# Always allow read/write-safe tools
case "${TOOL_NAME}" in
  Read|Glob|Grep|WebFetch|WebSearch|Write) exit 0 ;;
esac

# Always allow git operations
if printf '%s' "${TOOL_INPUT}" | grep -qE 'git '; then exit 0; fi

# No session file means no block
if [[ ! -f "${CURRENT_FILE}" ]]; then exit 0; fi
SESSION_FILE="$(cat "${CURRENT_FILE}" 2>/dev/null || true)"
if [[ -z "${SESSION_FILE}" || ! -f "${SESSION_FILE}" ]]; then exit 0; fi

# Deterministic decision count; never let parse/no-match crash the gate
COUNT=$(python3 -c "import json,sys
try:
    d=json.load(open(sys.argv[1], 'r', encoding='utf-8'))
    print(len(d.get('decisions', [])))
except Exception:
    print(0)
" "${SESSION_FILE}" 2>/dev/null || printf '0')

if [[ "${COUNT}" == "0" ]]; then
  echo "BTS GATE BLOCKED: no decisions recorded"
  exit 2
fi

exit 0
