#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BTS_DIR="${REPO_DIR}/_bts"
CURRENT_FILE="${BTS_DIR}/.current"

if [[ ! -f "${CURRENT_FILE}" ]]; then
  echo "No active BTS session to finalize."
  exit 0
fi

SESSION_FILE="$(cat "${CURRENT_FILE}" 2>/dev/null || true)"

if [[ -n "${SESSION_FILE}" && -f "${SESSION_FILE}" ]]; then
  FINALIZED_AT="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  python3 - "${SESSION_FILE}" "${FINALIZED_AT}" <<'PYEOF'
import json, sys
session_file, finalized_at = sys.argv[1], sys.argv[2]
with open(session_file, 'r', encoding='utf-8') as f:
    data = json.load(f)
data['finalized_at'] = finalized_at
data['status'] = 'complete'
with open(session_file, 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2)
print(f"BTS session finalized: {data['id']} ({len(data['decisions'])} decisions)")
PYEOF
else
  echo "WARNING: Session file not found; clearing stale pointer."
fi

rm -f "${CURRENT_FILE}"
