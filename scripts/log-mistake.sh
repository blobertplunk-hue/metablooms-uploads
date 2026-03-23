#!/usr/bin/env bash
# scripts/log-mistake.sh — append a dated mistake entry to .claude/CLAUDE.md
# Usage:
#   ./scripts/log-mistake.sh "what went wrong → what the fix was"
#   echo "description" | ./scripts/log-mistake.sh
#
# Called automatically by:
#   - Claude Code Stop hook (end of every session)
#   - Claude Code PostToolUse hook (on Bash exit code != 0)
#   - /mistake slash command
set -euo pipefail

CLAUDE_MD="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/.claude/CLAUDE.md"

# Read description from arg or stdin
if [[ $# -ge 1 && -n "${1:-}" ]]; then
  DESCRIPTION="$*"
elif [[ ! -t 0 ]]; then
  DESCRIPTION="$(cat)"
else
  echo "Usage: log-mistake.sh \"what went wrong → what the fix was\"" >&2
  exit 1
fi

if [[ -z "${DESCRIPTION}" ]]; then
  echo "log-mistake: empty description — skipping." >&2
  exit 0
fi

DATE="$(date -u +%Y-%m-%d)"
ENTRY="- ${DATE}: ${DESCRIPTION}"

if ! grep -qF "${ENTRY}" "${CLAUDE_MD}" 2>/dev/null; then
  # Insert after the last existing mistake entry, or after the Mistake Log header
  if grep -qE '^- [0-9]{4}-[0-9]{2}-[0-9]{2}:' "${CLAUDE_MD}"; then
    # Append after last dated entry
    sed -i "/^- [0-9]\{4\}-[0-9]\{2\}-[0-9]\{2\}:/{ h; d }; \${G; s/\n\(.*\)/\n\1\n${ENTRY}/; }" "${CLAUDE_MD}" 2>/dev/null \
      || echo -e "\n${ENTRY}" >> "${CLAUDE_MD}"
  else
    echo -e "\n${ENTRY}" >> "${CLAUDE_MD}"
  fi
  echo "Logged: ${ENTRY}"
else
  echo "Already logged — skipping duplicate."
fi
