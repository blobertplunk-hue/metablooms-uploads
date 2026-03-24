#!/usr/bin/env bash

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CURRENT_FILE="${REPO_DIR}/_bts/.current"
TOOL_NAME="${CLAUDE_TOOL_NAME:-}"
TOOL_INPUT="${CLAUDE_TOOL_INPUT:-}"

# ---- FAILSAFE BYPASS ----
if [[ "${BTS_BYPASS:-}" == "1" ]]; then exit 0; fi

# ---- ALWAYS ALLOW BTS ----
if echo "${TOOL_INPUT}" | grep -qF 'bts'; then exit 0; fi

# ---- ALWAYS ALLOW SAFE TOOLS ----
case "${TOOL_NAME}" in
  Read|Glob|Grep|WebFetch|WebSearch|Write) exit 0 ;;
esac

# ---- ALWAYS ALLOW GIT ----
if echo "${TOOL_INPUT}" | grep -q 'git '; then exit 0; fi

# ---- SESSION SAFE GUARDS ----
if [[ ! -f "${CURRENT_FILE}" ]]; then exit 0; fi

SESSION_FILE="$(cat "${CURRENT_FILE}" 2>/dev/null || true)"

if [[ -z "${SESSION_FILE}" || ! -f "${SESSION_FILE}" ]]; then exit 0; fi

# ---- SAFE DECISION COUNT ----
COUNT=$(python3 -c "import json,sys;
try:
 d=json.load(open(sys.argv[1]))
 print(len(d.get('decisions',[])))
except:
 print(0)
" "${SESSION_FILE}")

if [[ "${COUNT}" == "0" ]]; then
  echo "BTS GATE BLOCKED"
  exit 2
fi

exit 0
