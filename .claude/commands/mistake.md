---
name: mistake
description: Log a mistake to the Mistake Log in .claude/CLAUDE.md. Called automatically by hooks; also callable manually. Argument format: "what went wrong → what the fix was"
argument-hint: "what went wrong → what the fix was"
allowed-tools: Bash
---

Log the following mistake to `.claude/CLAUDE.md`:

**$ARGUMENTS**

Run the appropriate script for the current OS:

- Linux/macOS: `bash scripts/log-mistake.sh "$ARGUMENTS"`
- Windows: `pwsh -File scripts/log-mistake.ps1 "$ARGUMENTS"`

After logging, confirm the entry was written by reading the Mistake Log section of `.claude/CLAUDE.md`.

If $ARGUMENTS is empty, scan the current conversation for any errors, corrections, failed commands, or user-reported problems, and log each one as a separate entry.
