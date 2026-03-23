# Project Memory — MetaBlooms Uploads

## Boris Cherny Core Rules

- **Parallel agents:** Run independent subtasks in parallel; never serialize what can be parallelized.
- **Plan-first:** Use plan mode first (`/plan`). Only switch to auto-accept for well-scoped execution.
- **Verification loops:** After every change, tests and linters must pass before committing.
- **Self-updating:** When you make a mistake, append an entry to the Mistake Log below so you don't repeat it.
- **Fail-closed:** Never silently continue on error. Abort with a clear message.
- **Evidence over claims:** A receipt or test output proves execution; a comment or docstring does not.

## Repository Context

This is the **MetaBlooms OS** artifact repository — a governed, deterministic, artifact-first execution system.

Key constraints:

- Append-only commit chain: never amend published commits
- Every write must be tracked: `artifact_store.store() → read-back → hash-verified → receipt → commit_system.commit()`
- All artifacts include a SHA256 receipt in a paired `*_RECEIPT_*.json` file
- Freeze state documented in `KERNEL_ADOPTION_FREEZE_v4-1.json` — do not modify frozen components

## Commands

```bash
# Verify git status
git status

# Validate JSON artifacts
python3 -m json.tool <file>.json

# Compute SHA256 of an artifact
sha256sum <file>

# Run prettier formatter
prettier --write .
```

## Coding Standards

- JSON artifacts: 2-space indent, keys sorted by convention
- Bash scripts: `set -euo pipefail`, shellcheck-clean
- PowerShell scripts: `#Requires -Version 7.0`, `$ErrorActionPreference = 'Stop'`
- No silent failures; every error path must `throw` or `exit 1` with a message

## Aakash Gupta — PRD Writer

Use `/prd` to generate a structured Product Requirements Document:

- **Problem:** What is broken or missing?
- **Users:** Who is affected?
- **Goals:** Measurable outcomes
- **Non-goals:** Explicit exclusions
- **Success metrics:** How will we know we succeeded?
- **Milestones:** Ordered delivery steps

## Jacob Bartlett — Staff Engineer Review

Before finalizing any plan, spawn the `plan-review` subagent to critique the approach from a
Staff Engineer perspective. It will challenge:

- Scalability assumptions
- Security surface area
- Maintainability and coupling
- Missing edge cases
- Simpler alternatives

## Mistake Log

<!-- Claude: append entries here when an error is found and corrected. Format:
     - YYYY-MM-DD: [what went wrong] → [what the fix was]
-->

- 2026-03-23: Timed out writing a large file in one shot → Break large file writes into sections; never attempt to write >300 lines in a single Write tool call.
- 2026-03-23: Printed `git clone <repo>` placeholder instead of the actual repo URL → Always read `git remote get-url origin` first and substitute the real URL before showing any clone command to the user.
- 2026-03-23: Showed the local proxy URL (`http://local_proxy@127.0.0.1:37017/...`) as if it were usable from outside the sandbox → That URL only works inside the Claude Code server. Never present it to the user as a clone URL. If no public URL exists, say so explicitly.
- 2026-03-23: Delivered a `.sh` bash script to a Windows user without a PowerShell equivalent → Always ask or detect the user's OS before writing setup scripts. Windows users need `.ps1`; never assume bash.
- 2026-03-23: Gave `pwsh -File setup-claude.ps1` (no path prefix) → PowerShell requires `.\` for local scripts: always use `pwsh -File .\setup-claude.ps1`.
- 2026-03-23: After being asked for a "one-shot copy-paste", still delivered a command that referenced a `.ps1` file the user didn't have locally → A one-shot means fully self-contained inline code. Never reference an external file in a one-shot command.
- 2026-03-23: One-shot assumed `npm` was installed and crashed with "npm not found" → Always guard against missing prerequisites. On Windows 11, use `winget install OpenJS.NodeJS.LTS` to install Node.js if `npm` is not found, then refresh `$env:PATH` before continuing.
