#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BTS_DIR="${REPO_DIR}/_bts"
CURRENT_FILE="${BTS_DIR}/.current"

if [[ -z "${1:-}" ]]; then
  echo "Usage: bash scripts/bts-record.sh '{\"level\":\"prompt\",\"context\":\"...\",\"options\":[...],\"selected\":\"...\",\"criteria\":[\"...\"],\"confidence\":0.9}'" >&2
  exit 1
fi

if [[ ! -f "${CURRENT_FILE}" ]]; then
  echo "ERROR: No active BTS session. Run: bash scripts/bts-init.sh" >&2
  exit 1
fi

SESSION_FILE="$(cat "${CURRENT_FILE}" 2>/dev/null || true)"
if [[ -z "${SESSION_FILE}" || ! -f "${SESSION_FILE}" ]]; then
  echo "ERROR: Session file missing or corrupt. Run: bash scripts/bts-init.sh" >&2
  exit 1
fi

python3 - "${1}" "${SESSION_FILE}" <<'PYEOF'
import json, sys
raw, session_file = sys.argv[1], sys.argv[2]
try:
    decision = json.loads(raw)
except json.JSONDecodeError as e:
    print(f"ERROR: Invalid JSON — {e}", file=sys.stderr)
    sys.exit(1)
with open(session_file, 'r', encoding='utf-8') as f:
    data = json.load(f)
data['decisions'].append(decision)
with open(session_file, 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2)
print(f"Decision recorded. Total this session: {len(data['decisions'])}")
PYEOF
