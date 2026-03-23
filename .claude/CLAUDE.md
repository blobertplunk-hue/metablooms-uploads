# Project Memory — MetaBlooms Uploads

---

## LAYER 0 — BTS (Behind The Scenes) — MANDATORY, PRE-OUTPUT

**BTS is not optional. Zero decisions recorded = protocol violation.**

BTS is a live, enforced decision trace. Every meaningful choice must be recorded
BEFORE output is produced. If BTS is not written, do not respond.

### What BTS captures

A decision = multiple options exist → one selected → others rejected → criteria used.

```json
{
  "id": "D-001",
  "level": "prompt|task|micro",
  "context": "what choice was being made",
  "options": [
    {
      "name": "A",
      "pros": ["..."],
      "cons": ["..."],
      "selected": false,
      "reason": "..."
    },
    {
      "name": "B",
      "pros": ["..."],
      "cons": ["..."],
      "selected": true,
      "reason": "..."
    }
  ],
  "selected": "B",
  "criteria": ["clarity", "maintainability"],
  "confidence": 0.85
}
```

### Three levels — all must run

| Level      | Scope            | Examples                                      |
| ---------- | ---------------- | --------------------------------------------- |
| **Prompt** | Every prompt     | How to interpret it, response format, depth   |
| **Task**   | Structured work  | Which protocol, which tools, which stages     |
| **Micro**  | Inside execution | Algorithm, pattern, variable names, structure |

### How to record

```bash
bash scripts/bts-record.sh '{"level":"prompt","context":"...","options":[...],"selected":"...","criteria":["..."],"confidence":0.9}'
```

Or use `/bts` to batch-record all decisions for the current turn.

### Session lifecycle (handled by hooks)

- **SessionStart** → `bash scripts/bts-init.sh` (creates `_bts/sessions/SESSION_<id>.json`)
- **Stop** → `bash scripts/bts-finalize.sh` (marks session complete, clears `.current`)
- Session files live in `_bts/sessions/` — never delete them; they are the decision history.

---

## LAYER 1 — Core Execution Rules (Boris Cherny)

- **Parallel agents:** Run independent subtasks in parallel. Never serialize what can be parallelized.
- **Plan-first:** Use plan mode (`/plan`) before any significant change. Only switch to auto-accept for well-scoped execution. Spawn `plan-review` subagent before finalizing.
- **Verification loops:** After every change, tests and linters must pass before committing. Use `/verify`.
- **Fail-closed:** Never silently continue on error. Abort with a clear message and exit 1.
- **Evidence over claims:** A receipt, test output, or `sha256sum` proves execution. A comment or docstring does not.
- **Mistake logging:** When any mistake is discovered (user correction, failed command, wrong output), immediately run `bash scripts/log-mistake.sh "what went wrong → what the fix was"`. Non-negotiable. See Layer 4.

---

## LAYER 2 — Repository Constraints

This is the **MetaBlooms OS** artifact repository — governed, deterministic, artifact-first.

- Append-only commit chain: **never amend published commits**
- Every write: `artifact_store.store() → read-back → hash-verified → receipt → commit`
- All artifacts include a SHA256 receipt in a paired `*_RECEIPT_*.json` file
- Freeze state in `KERNEL_ADOPTION_FREEZE_v4-1.json` — do not modify frozen components

```bash
git status                          # check state
python3 -m json.tool <file>.json    # validate JSON
sha256sum <file>                    # compute receipt hash
prettier --write .                  # format
```

---

## LAYER 3 — Coding Standards

- JSON: 2-space indent, keys sorted by convention
- Bash: `set -euo pipefail`, shellcheck-clean, no silent failures
- PowerShell: `#Requires -Version 7.0`, `$ErrorActionPreference = 'Stop'`
- Every error path must `throw` or `exit 1` with a message
- File writes >300 lines: break into sections, never one shot
- One-shot commands: must be fully self-contained — never reference a file the user doesn't have

---

## LAYER 4 — Platform Awareness (learned this session)

**Before writing any script or command, detect the user's OS.**

| Rule                          | Detail                                                                                                   |
| ----------------------------- | -------------------------------------------------------------------------------------------------------- |
| Never assume bash             | Windows users need `.ps1`. Always provide both or ask.                                                   |
| Never show localhost URLs     | `127.0.0.1` / `local_proxy` URLs are sandbox-internal only. Never present to user as usable.             |
| Always read actual remote URL | Run `git remote get-url origin` before printing any clone command.                                       |
| `.\` required on Windows      | PowerShell requires `.\script.ps1`, not `script.ps1`.                                                    |
| One-shot = inline only        | A one-shot copy-paste must contain everything. No file references.                                       |
| npm may not exist             | On Windows, guard with `winget install OpenJS.NodeJS.LTS` if `npm` not found. Refresh `$env:PATH` after. |

---

## LAYER 5 — Specialist Protocols

### Aakash Gupta — PRD Writer

Use `/prd "[description]"` to generate:
Problem · Users · Goals · Non-goals · Success metrics · Milestones

### Jacob Bartlett — Staff Engineer Review

Before finalizing any plan, spawn `plan-review` subagent. It challenges:
scalability, security, maintainability, edge cases, simpler alternatives.

---

## LAYER 6 — Available Commands & Agents

| Command           | Purpose                                      |
| ----------------- | -------------------------------------------- |
| `/bts`            | Record BTS decisions (mandatory pre-output)  |
| `/mistake "desc"` | Log a mistake to the Mistake Log             |
| `/verify`         | Run all checks — JSON, lint, tests, receipts |
| `/prd "desc"`     | Generate structured PRD                      |
| `/commit-push-pr` | Stage → commit → push → open PR              |

| Agent             | Purpose                                    |
| ----------------- | ------------------------------------------ |
| `plan-review`     | Staff Engineer critique before execution   |
| `code-simplifier` | Simplify and refactor after implementation |
| `verify-app`      | Full verification suite                    |

---

## Mistake Log

<!-- Format: - YYYY-MM-DD: [what went wrong] → [what the fix was] -->
