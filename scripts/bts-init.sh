#!/usr/bin/env bash
# scripts/bts-init.sh — initialise a new BTS session file
# Called by the SessionStart hook at the start of every Claude Code session.
# Writes _bts/.current with the session ID so other scripts know where to append.
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BTS_DIR="${REPO_DIR}/_bts/sessions"
CURRENT_FILE="${REPO_DIR}/_bts/.current"

mkdir -p "${BTS_DIR}"

SESSION_ID="SESSION_$(date -u +%Y%m%d_%H%M%S)"
SESSION_FILE="${BTS_DIR}/${SESSION_ID}.json"

python3 - "${SESSION_FILE}" "${SESSION_ID}" <<'PYEOF'
import json, sys
from datetime import datetime, timezone

path, sid = sys.argv[1], sys.argv[2]
doc = {
    "session_id": sid,
    "started_utc": datetime.now(timezone.utc).isoformat(),
    "status": "active",
    "decisions": []
}
with open(path, "w") as f:
    json.dump(doc, f, indent=2)
    f.write("\n")
print(path)
PYEOF

echo "${SESSION_FILE}" > "${CURRENT_FILE}"
echo "BTS session initialised: ${SESSION_ID}"
