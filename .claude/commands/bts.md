---
name: bts
description: Record BTS (Behind The Scenes) decisions for the current prompt. MANDATORY — call this before producing any substantive output. With no argument, records all decisions made so far this turn. With a JSON argument, appends that single decision.
argument-hint: '[{"context":"...","selected":"..."}] or empty to auto-record'
allowed-tools: Bash, Read
---

## BTS is mandatory. No output before decisions are recorded.

### If $ARGUMENTS is empty — record all decisions for this prompt:

For the current prompt, identify every meaningful decision made at all three levels:

**Level 1 — Prompt:** How did I interpret this? What response format? What depth?
**Level 2 — Task:** Which protocol/approach? Which tools? Which stages?
**Level 3 — Micro:** Inside execution — which algorithm, pattern, structure, naming?

For EACH decision, call:

```bash
bash scripts/bts-record.sh '{"level":"prompt|task|micro","context":"...","options":[{"name":"A","pros":["..."],"cons":["..."],"selected":false,"reason":"..."},{"name":"B","pros":["..."],"cons":["..."],"selected":true,"reason":"..."}],"selected":"B","criteria":["..."],"confidence":0.9}'
```

### If $ARGUMENTS is a JSON decision object — append it directly:

```bash
bash scripts/bts-record.sh '$ARGUMENTS'
```

### After recording, confirm:

```bash
cat "$(cat _bts/.current 2>/dev/null)" 2>/dev/null | python3 -m json.tool | tail -30
```

### Rule:

If the session file does not exist yet, `bts-record.sh` will auto-initialise it.
Zero decisions recorded = protocol violation. Log it with `/mistake`.
