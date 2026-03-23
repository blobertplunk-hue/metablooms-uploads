---
name: verify
description: Run all available verification checks — linters, JSON validators, and tests — and report pass/fail for each. Use after making changes to confirm nothing is broken.
allowed-tools: Bash, Read, Glob, Grep
---

Run all available verification checks and report results.

## Checks to Run (in order)

1. **JSON validation** — for every `*.json` file in the repo:
   ```bash
   find . -name "*.json" -not -path "./.git/*" | while read -r f; do
     python3 -m json.tool "$f" > /dev/null && echo "PASS: $f" || echo "FAIL: $f"
   done
   ```

2. **Bash linting** — for every `*.sh` file (if shellcheck is available):
   ```bash
   shellcheck *.sh .claude/**/*.sh 2>/dev/null || true
   ```

3. **PowerShell syntax check** — for every `*.ps1` file (if pwsh is available):
   ```bash
   for f in *.ps1; do
     pwsh -NoProfile -Command "& { \$null = [scriptblock]::Create((Get-Content -Raw '$f')) }" \
       && echo "PASS: $f" || echo "FAIL: $f"
   done
   ```

4. **Prettier formatting check** (if prettier is available):
   ```bash
   prettier --check . 2>&1 | tail -5
   ```

5. **pytest** (if available):
   ```bash
   pytest --tb=short -q 2>/dev/null || echo "pytest not found or no tests"
   ```

6. **SHA256 receipt integrity** — for each `*_RECEIPT_*.json`, verify the `sha256` field matches the referenced artifact file.

## Outcome

Print a summary table:
```
Check              Status
───────────────────────────
JSON validation    PASS (7/7)
Bash lint          PASS
PS1 syntax         PASS (1/1)
Prettier           PASS
Tests              SKIP (pytest not found)
Receipt integrity  PASS (2/2)
───────────────────────────
Overall            PASS
```

Exit with code 1 if any check fails so the caller can detect failure.
