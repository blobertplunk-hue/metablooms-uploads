#!/usr/bin/env bash
# scripts/bts-finalize.sh — close the current BTS session
# Called by the Stop hook at end of every session.
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CURRENT_FILE="${REPO_DIR}/_bts/.current"

if [[ ! -f "${CURRENT_FILE}" ]]; then
  echo "BTS: no active session to finalise."
  exit 0
fi

SESSION_FILE="$(cat "${CURRENT_FILE}")"

if [[ ! -f "${SESSION_FILE}" ]]; then
  echo "BTS: session file missing — skipping."
  rm -f "${CURRENT_FILE}"
  exit 0
fi

python3 - "${SESSION_FILE}" <<'PYEOF'
import json, sys
from datetime import datetime, timezone

path = sys.argv[1]
with open(path) as f:
    session = json.load(f)

session["status"] = "complete"
session["ended_utc"] = datetime.now(timezone.utc).isoformat()
session["decision_count"] = len(session["decisions"])

with open(path, "w") as f:
    json.dump(session, f, indent=2)
    f.write("\n")

print(f"BTS finalised: {session['session_id']} — {session['decision_count']} decision(s) recorded")
PYEOF

rm -f "${CURRENT_FILE}"
