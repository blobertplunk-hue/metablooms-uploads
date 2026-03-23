---
name: commit-push-pr
description: Stage all changes, commit with a conventional commit message, push the current branch, and open a pull request. Use after completing a feature or fix.
allowed-tools: Bash, Read, Glob
---

Stage, commit, push, and open a PR for the current branch.

## Steps

1. Run `git status` to review what has changed.
2. Run `git diff --stat` to summarise the changes.
3. Draft a conventional commit message (type: feat|fix|docs|chore|refactor|test, scope optional, imperative subject ≤72 chars).
4. Run `git add -p` or `git add <specific files>` — never `git add .` (avoids committing secrets or generated files).
5. Run `git commit -m "<message>"`.
6. Run `git push -u origin <current-branch>`.
7. If `gh` is available, run `gh pr create --title "<message>" --body "## Summary\n$ARGUMENTS\n\n## Test plan\n- [ ] Verify changes work as intended"`.
8. If `gh` is not available, print the GitHub URL to create a PR manually.

## Conventions

- Do not skip pre-commit hooks (`--no-verify` is forbidden).
- Do not amend published commits.
- If push fails with 403, check that the branch name starts with `claude/`.
- Append the session URL to every commit message:
  `https://claude.ai/code/session_01DwbyLa55aQbDJn1HpZVK8U`
