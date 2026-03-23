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
