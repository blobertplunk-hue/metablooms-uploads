#!/usr/bin/env bash
# scripts/bts-auto-record.sh — PreToolUse hook: auto-log every tool call to BTS
#
# Reads CLAUDE_TOOL_NAME and CLAUDE_TOOL_INPUT from the environment (set by
# Claude Code before each PreToolUse hook runs) and appends a micro-level BTS
# decision entry so that every action is traceable without manual /bts calls.
#
# Skips: BTS-internal tools, read-only tools (Read/Glob/Grep/WebFetch/WebSearch),
#        and git status/log queries — these are lookups, not decisions.

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TOOL="${CLAUDE_TOOL_NAME:-}"
INPUT="${CLAUDE_TOOL_INPUT:-}"

# --- Skip list -----------------------------------------------------------

# Skip BTS infra itself (avoid infinite recursion)
case "${INPUT}" in
  *bts-record*|*bts-init*|*bts-gate*|*bts-finalize*|*bts-auto-record*|*log-mistake*) exit 0 ;;
esac

# Skip pure read-only / lookup tools — no decision is being made
case "${TOOL}" in
  Read|Glob|Grep|WebFetch|WebSearch) exit 0 ;;
esac

# Skip read-only git queries
if printf '%s' "${INPUT}" | grep -qE 'git (status|log|diff|show|ls-files|remote get-url)'; then
  exit 0
fi

# --- Build a context string from the tool + input ------------------------

CONTEXT=""
case "${TOOL}" in
  Bash)
    # Trim to first 120 chars so JSON stays readable
    CONTEXT="Bash: $(printf '%s' "${INPUT}" | head -c 120)"
    ;;
  Edit)
    FILE=$(printf '%s' "${INPUT}" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('file_path','?'))" 2>/dev/null || echo "?")
    CONTEXT="Edit file: ${FILE}"
    ;;
  Write)
    FILE=$(printf '%s' "${INPUT}" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('file_path','?'))" 2>/dev/null || echo "?")
    CONTEXT="Write file: ${FILE}"
    ;;
  Agent)
    DESC=$(printf '%s' "${INPUT}" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('description','?'))" 2>/dev/null || echo "?")
    CONTEXT="Spawn agent: ${DESC}"
    ;;
  *)
    CONTEXT="${TOOL}: $(printf '%s' "${INPUT}" | head -c 80)"
    ;;
esac

# --- Emit a minimal BTS micro-decision -----------------------------------

DECISION=$(python3 -c "
import json, sys
context = sys.argv[1]
tool    = sys.argv[2]
entry = {
    'level':    'micro',
    'context':  context,
    'options':  [
        {'name': 'do-it',   'selected': True,  'reason': 'required to fulfil user request'},
        {'name': 'skip-it', 'selected': False, 'reason': 'would leave the task incomplete'}
    ],
    'selected':   'do-it',
    'criteria':   ['task-completion', 'user-intent'],
    'confidence': 0.95
}
print(json.dumps(entry))
" "${CONTEXT}" "${TOOL}" 2>/dev/null)

if [[ -n "${DECISION}" ]]; then
  bash "${REPO_DIR}/scripts/bts-record.sh" "${DECISION}" 2>/dev/null || true
fi

exit 0
