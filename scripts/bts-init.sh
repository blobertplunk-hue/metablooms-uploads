#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BTS_DIR="${REPO_DIR}/_bts"
SESSIONS_DIR="${BTS_DIR}/sessions"

mkdir -p "${SESSIONS_DIR}"

SESSION_ID="SESSION_$(date -u +%Y%m%dT%H%M%SZ)_$$"
SESSION_FILE="${SESSIONS_DIR}/${SESSION_ID}.json"
STARTED_AT="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

python3 - "${SESSION_ID}" "${SESSION_FILE}" "${STARTED_AT}" <<'PYEOF'
import json, sys
session_id, session_file, started_at = sys.argv[1], sys.argv[2], sys.argv[3]
data = {
    "decisions": [],
    "id": session_id,
    "started_at": started_at,
    "status": "active"
}
with open(session_file, 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2)
PYEOF

echo "${SESSION_FILE}" > "${BTS_DIR}/.current"

echo "BTS session initialized: ${SESSION_ID}"
echo "Session file: ${SESSION_FILE}"
