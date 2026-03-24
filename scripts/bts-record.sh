#!/usr/bin/env bash
# scripts/bts-record.sh — append a decision to the current BTS session
#
# Usage:
#   bash scripts/bts-record.sh '<json>'
#
# Minimal JSON:
#   {
#     "level": "prompt|task|micro",
#     "context": "what choice was being made",
#     "options": [...],
#     "selected": "B",
#     "criteria": ["clarity"],
#     "confidence": 0.85
#   }
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CURRENT_FILE="${REPO_DIR}/_bts/.current"

if [[ ! -f "${CURRENT_FILE}" ]]; then
  bash "${REPO_DIR}/scripts/bts-init.sh" >/dev/null
fi

SESSION_FILE="$(cat "${CURRENT_FILE}")"

if [[ ! -f "${SESSION_FILE}" ]]; then
  bash "${REPO_DIR}/scripts/bts-init.sh" >/dev/null
  SESSION_FILE="$(cat "${CURRENT_FILE}")"
fi

DECISION_JSON="${1:-}"
if [[ -z "${DECISION_JSON}" ]]; then
  echo "bts-record: empty decision — skipping." >&2
  exit 0
fi

python3 - "${SESSION_FILE}" "${DECISION_JSON}" <<'PYEOF'
import json, sys

session_path = sys.argv[1]
decision_raw = sys.argv[2]

try:
    decision = json.loads(decision_raw)
except json.JSONDecodeError as e:
    print(f"bts-record: invalid JSON — {e}", file=sys.stderr)
    sys.exit(1)

with open(session_path) as f:
    session = json.load(f)

idx = len(session["decisions"]) + 1
decision.setdefault("id", f"D-{idx:03d}")

session["decisions"].append(decision)

with open(session_path, "w") as f:
    json.dump(session, f, indent=2)
    f.write("\n")

print(f"BTS recorded {decision['id']}: {decision.get('context', '')}")
PYEOF
