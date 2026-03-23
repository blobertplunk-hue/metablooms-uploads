#!/usr/bin/env bash
# shellcheck shell=bash
#
# open-sessions.sh — Open N parallel Claude Code sessions in separate terminal tabs/windows.
#
# Usage:
#   ./.claude/open-sessions.sh [N]        # Open N sessions (default: 5)
#   ./.claude/open-sessions.sh 10         # Open 10 sessions
#
# Supported terminals:
#   macOS  : Terminal.app (default), Ghostty (if installed), iTerm2 (if installed)
#   Linux  : gnome-terminal, xterm (fallback)
#   Windows: Not supported from bash; use Windows Terminal: wt new-tab pwsh -c claude
#
# Idempotence: If N or more `claude` processes are already running, prints a
# message and exits without opening new windows.

set -euo pipefail

N="${1:-5}"

# ── Idempotency check ────────────────────────────────────────────────────────
existing=$(pgrep -c claude 2>/dev/null || echo 0)
if [[ "$existing" -ge "$N" ]]; then
  echo "INFO: $existing claude process(es) already running (requested $N). Skipping."
  exit 0
fi

to_open=$(( N - existing ))
echo "Opening $to_open Claude session(s) ($existing already running, target $N)..."

# ── OS detection ─────────────────────────────────────────────────────────────
os="linux"
if [[ "${OSTYPE:-}" == "darwin"* ]]; then
  os="macos"
fi

# ── Open sessions ────────────────────────────────────────────────────────────
for i in $(seq 1 "$to_open"); do
  if [[ "$os" == "macos" ]]; then
    # Prefer Ghostty, then iTerm2, then Terminal.app
    if command -v ghostty &>/dev/null; then
      ghostty --new-window -- claude &
    elif [[ -d "/Applications/iTerm.app" ]]; then
      osascript -e 'tell application "iTerm2" to create window with default profile command "claude"' &
    else
      osascript -e 'tell application "Terminal" to do script "claude"' &
    fi
  else
    # Linux: prefer gnome-terminal, fall back to xterm
    if command -v gnome-terminal &>/dev/null; then
      gnome-terminal --tab -- bash -c "claude; exec bash" 2>/dev/null &
    elif command -v xterm &>/dev/null; then
      xterm -e "claude; bash" &
    else
      echo "WARN: No supported terminal emulator found. Install gnome-terminal or xterm."
      echo "      You can start Claude manually with: claude"
    fi
  fi
  sleep 0.3
done

echo "Done. $to_open session(s) launched."
