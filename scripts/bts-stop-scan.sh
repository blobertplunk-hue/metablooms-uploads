#!/usr/bin/env bash
# scripts/bts-stop-scan.sh — Stop hook: scan BTS session for decision gaps
#
# Runs at session end (Stop hook).  Reads the current BTS session file and:
#   1. Flags if decision_count == 0 (zero decisions = protocol violation)
#   2. Flags if any decision has confidence < 0.6 (low-confidence choices)
#   3. Flags decisions with no options recorded (incomplete trace)
#
# Each gap found is logged via log-mistake.sh and printed for the user.
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CURRENT_FILE="${REPO_DIR}/_bts/.current"

if [[ ! -f "${CURRENT_FILE}" ]]; then
  exit 0
fi

SESSION_FILE="$(cat "${CURRENT_FILE}" 2>/dev/null || echo '')"
if [[ -z "${SESSION_FILE}" || ! -f "${SESSION_FILE}" ]]; then
  exit 0
fi

python3 - "${SESSION_FILE}" "${REPO_DIR}" <<'PYEOF'
import json, sys, subprocess
from datetime import datetime, timezone

session_path = sys.argv[1]
repo_dir     = sys.argv[2]
log_script   = f"{repo_dir}/scripts/log-mistake.sh"

def log(msg):
    try:
        subprocess.run(["bash", log_script, msg], cwd=repo_dir, check=False, timeout=10)
    except Exception:
        pass

with open(session_path) as f:
    session = json.load(f)

decisions = session.get("decisions", [])
gaps = []

# Gap type 1: zero decisions
if len(decisions) == 0:
    gaps.append("BTS_ZERO_DECISIONS: No decisions were recorded this session — protocol violation")

# Gap type 2: low confidence decisions
for d in decisions:
    conf = d.get("confidence", 1.0)
    ctx  = d.get("context", "unknown")
    if isinstance(conf, (int, float)) and conf < 0.6:
        gaps.append(f"BTS_LOW_CONFIDENCE ({conf:.2f}): '{ctx}'")

# Gap type 3: decisions with no options (incomplete trace)
for d in decisions:
    opts = d.get("options", [])
    ctx  = d.get("context", "unknown")
    if len(opts) < 2:
        gaps.append(f"BTS_INCOMPLETE_OPTIONS: '{ctx}' has {len(opts)} option(s) (need ≥2)")

# Gap type 4: levels not covered (should have prompt + task + micro)
levels_seen = {d.get("level") for d in decisions}
required_levels = {"prompt", "task", "micro"}
missing_levels  = required_levels - levels_seen
if missing_levels and len(decisions) > 0:
    gaps.append(f"BTS_MISSING_LEVELS: {sorted(missing_levels)} not represented")

if gaps:
    print(f"\n[bts-stop-scan] {len(gaps)} BTS gap(s) detected in {session.get('session_id','?')}:")
    for g in gaps:
        print(f"  GAP: {g}")
        log(f"BTS stop-scan detected → {g}")
else:
    print(f"[bts-stop-scan] OK — {len(decisions)} decision(s) across "
          f"{sorted(levels_seen)} levels. No gaps.")
PYEOF
