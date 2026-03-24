# MetaBlooms MPP — S-Tier Build Prompt for Claude Code

## CONTEXT YOU MUST READ FIRST

You are building inside an existing MetaBlooms OS. The system has:
- `MPP_RUNTIME.py` — governance shell with real order enforcement, DEBUGGING exit contracts, cycle tracking. **Keep this. Do not rewrite it.**
- `SEE_ENGINE.py` + `HOST_WEB_RUNNER_BRIDGE.py` — real fail-closed SEE with host-injected web runner. **Keep this.**
- `EXECUTION_OBSERVER_ENGINE.py` — `@trace_span` decorator, span hierarchy, artifact recording. **Keep this.**
- `GLOBAL_EXECUTION_GATE.py` — env-var gate, `enter_pipeline()`/`exit_pipeline()`. **Keep this.**
- `FIR.py` — Forced Improvement Runtime. Measures 4 real fitness criteria from actual BTS log and MPP receipts. Produces `PatchProposal` objects. Commits or rejects sessions at threshold 0.60. **This is your improvement loop model.**

The MPP has 14 stages. 5 are mandatory: **SEE, CDR, IMPLEMENTATION, VERIFICATION, ECL**.
Currently SEE has a real engine. CDR, IMPLEMENTATION, VERIFICATION, ECL are stubs returning `{"ok": True}`.
All optional stages (MMD, DRS, OFM, ADS, UXR, NUF, SSO, RRP, DEBUGGING) are skipped.

**Your job: build S-tier stage engines for all 5 mandatory stages, wire them into MPP_RUNTIME, and implement the recursive improvement loop that FIR drives.**

---

## PHASE 0 — RESEARCH (MANDATORY BEFORE ANY CODE)

Use the SEE host bridge to research each of these before writing any stage engine.
Call `run_see(query)` with the injected web runner for each:

1. `"CDR coding done right constraints before implementation LLM governance"`
2. `"MPP mandatory process pipeline stage gate enforcement pattern"`
3. `"VERIFICATION stage erac council vote quorum LLM output quality"`
4. `"ECL end condition lock never skippable exit invariant"`
5. `"recursive improvement loop fitness gate commit threshold software quality"`

Record all evidence in `state/MPP_BUILD_RESEARCH.json` with this schema:
```json
{
  "query": "...",
  "result_hash": "...",
  "key_findings": ["...", "..."],
  "applied_to_stage": "CDR|VERIFICATION|ECL|..."
}
```

Do not write a single stage engine until this research is complete and recorded.

---

## PHASE 1 — STAGE ENGINES (BUILD IN THIS ORDER)

### 1.1 CDR_STAGE_ENGINE.py

CDR = Coding Done Right. Runs before IMPLEMENTATION. Forces constraint declaration before execution.

**Contract:**
```python
REQUIRES = ["SEE_ENGINE", "EXECUTION_OBSERVER_ENGINE"]
PROVIDES = ["cdr_constraints", "cdr_receipt"]

@trace_span("CDR")
def run_cdr(task: dict, see_evidence: dict) -> dict:
    """
    Input: task dict + SEE evidence from prior stage
    Output: {
        "constraints": [...],      # list of specific, testable constraints
        "forbidden": [...],        # what must NOT happen
        "success_criteria": [...], # how VERIFICATION will judge IMPLEMENTATION
        "cdr_receipt": {...}       # SHA256 of constraints + timestamp
    }
    Invariants:
    - constraints must be non-empty or raise CDRViolation
    - every constraint must reference a specific artifact or behavior
    - no constraint may contain "good", "clean", "appropriate" (vague)
    - receipt must be written before returning
    """
```

**Rubric for CDR output (used by VERIFICATION):**
- Specificity: every constraint is testable (4) vs references general quality (1)
- Coverage: constraints cover all SEE findings (4) vs misses known issues (1)  
- Actionability: IMPLEMENTATION can execute against constraints (4) vs ambiguous (1)

### 1.2 IMPLEMENTATION_STAGE_ENGINE.py

Replaces the stub. Executes against CDR constraints. Produces real artifacts.

**Contract:**
```python
REQUIRES = ["CDR_STAGE_ENGINE", "EXECUTION_OBSERVER_ENGINE", "VERIFIED_WRITE_v3"]
PROVIDES = ["implementation_artifacts", "implementation_receipt"]

@trace_span("IMPLEMENTATION")
def run_implementation(task: dict, cdr_output: dict) -> dict:
    """
    Input: task + CDR constraints
    Output: {
        "artifacts": [path, ...],   # actual files written via guarded_write
        "constraint_coverage": {},  # which CDR constraints were addressed
        "unaddressed": [...],       # constraints not covered (triggers DEBUGGING)
        "implementation_receipt": {
            "artifact_hashes": {...},
            "constraint_map": {...},
            "timestamp": "..."
        }
    }
    Invariants:
    - every artifact write goes through guarded_write (no raw file.write)
    - every CDR constraint must appear in constraint_coverage
    - unaddressed constraints > 0 → implementation is PARTIAL, not COMPLETE
    - receipt SHA256 must match artifacts at time of VERIFICATION
    """
```

### 1.3 VERIFICATION_STAGE_ENGINE.py

Replaces the stub. Runs ERAC scan + council vote.

**Contract:**
```python
REQUIRES = ["CDR_STAGE_ENGINE", "IMPLEMENTATION_STAGE_ENGINE", 
            "erac_engine", "council_engine", "EXECUTION_OBSERVER_ENGINE"]
PROVIDES = ["verification_verdict", "verification_receipt"]

@trace_span("VERIFICATION")
def run_verification(task: dict, cdr_output: dict, impl_output: dict) -> dict:
    """
    Input: task + CDR constraints + IMPLEMENTATION artifacts
    Output: {
        "verdict": "PASS"|"FAIL"|"ESCALATE",
        "erac_result": {...},      # ERAC-001 through ERAC-004 scan
        "council_votes": {...},    # RATIONALITY, RELIABILITY, ETHICS, BUILDER
        "quorum_met": bool,        # >= 85% weighted quorum
        "constraint_verification": {},  # each CDR constraint: met/unmet
        "verification_receipt": {...}
    }
    Invariants:
    - ERAC scan runs on ALL IMPLEMENTATION artifacts, not summary
    - council vote requires all 4 councils with rationale
    - quorum < 85% → FAIL (not PARTIAL)
    - any CDR constraint unmet → FAIL
    - receipt anchors artifact hashes from IMPLEMENTATION receipt
    """
```

**ERAC checks to implement:**
- ERAC-001: No claim without evidence artifact (checks implementation artifacts)
- ERAC-002: No inference without SEE anchoring (checks reasoning against SEE evidence)
- ERAC-003: No failure without root cause (checks unaddressed CDR constraints)
- ERAC-004: No blame-shifting (implementation must not cite external limitations for internal failures)

### 1.4 ECL_STAGE_ENGINE.py

End Condition Lock. Never skippable. The final gate.

**Contract:**
```python
REQUIRES = ["VERIFICATION_STAGE_ENGINE", "FIR", "BTS", "EXECUTION_OBSERVER_ENGINE"]
PROVIDES = ["ecl_lock", "fir_result", "coevolution_entry"]

@trace_span("ECL")
def run_ecl(task: dict, verification_output: dict, 
            runtime_root: str, bts, ledger) -> dict:
    """
    Input: task + VERIFICATION verdict + runtime root for FIR
    Output: {
        "ecl_status": "LOCKED"|"BLOCKED",
        "fir_result": FIRResult.to_dict(),
        "session_committed": bool,
        "improvement_delta": float|None,
        "patch_proposals": [...],   # FIR proposals for next session
        "ecl_receipt": {...}
    }
    Invariants:
    - ECL NEVER runs if VERIFICATION verdict != PASS
    - FIR.evaluate_session() MUST run — no skip allowed
    - If FIR returns INSUFFICIENT_DATA → ECL status = BLOCKED (not LOCKED)
    - If FIR score < 0.60 → session REJECTED, proposals written, ECL BLOCKED
    - If FIR score >= 0.60 → session COMMITTED, coevolution entry written
    - ECL receipt must include FIR fitness composite score
    - BLOCKED ECL does not prevent next session — it informs it
    """
```

---

## PHASE 2 — MPP WIRING

Update `MPP_RUNTIME.py` `run_stage()` to replace selftest handlers with real engine calls.

**Replace the selftest handler block with:**

```python
def _dispatch_stage(self, stage: str, task: dict, stage_outputs: dict, 
                    runtime_root: str, bts, ledger) -> dict:
    """
    Routes each stage to its engine. Returns handler_output for run_stage().
    This is the ONLY place stage engines are called from MPP.
    """
    if stage == "SEE":
        from SEE_ENGINE import run_see
        query = task.get("see_query", task.get("description", ""))
        return {"findings": run_see(query), "query": query}
    
    elif stage == "CDR":
        from CDR_STAGE_ENGINE import run_cdr
        see_evidence = stage_outputs.get("SEE", {}).get("payload", {})
        return run_cdr(task, see_evidence)
    
    elif stage == "IMPLEMENTATION":
        from IMPLEMENTATION_STAGE_ENGINE import run_implementation
        cdr_output = stage_outputs.get("CDR", {}).get("payload", {})
        return run_implementation(task, cdr_output)
    
    elif stage == "VERIFICATION":
        from VERIFICATION_STAGE_ENGINE import run_verification
        cdr_output = stage_outputs.get("CDR", {}).get("payload", {})
        impl_output = stage_outputs.get("IMPL", {}).get("payload", {})
        return run_verification(task, cdr_output, impl_output)
    
    elif stage == "ECL":
        from ECL_STAGE_ENGINE import run_ecl
        verif_output = stage_outputs.get("VERIFICATION", {}).get("payload", {})
        return run_ecl(task, verif_output, runtime_root, bts, ledger)
    
    else:
        return {"skip": True, "reason": f"optional_stage_{stage}"}
```

---

## PHASE 3 — RECURSIVE IMPROVEMENT LOOP

This is the FIR-driven improvement cycle. It mirrors FIR's architecture applied to MPP stage quality.

**MPP_IMPROVEMENT_LOOP.py** — new engine:

```python
"""
MPP Improvement Loop — SIE → Sandcrawler → SEE → CDR → IMPL → VERIFY → ECL
Recursive improvement using FIR fitness as the termination signal.

Loop contract:
  MAX_ITERATIONS = 3 (mirrors FIR's bounded recursion)
  IMPROVEMENT_THRESHOLD = 0.10 (minimum delta to justify another iteration)
  COMMIT_THRESHOLD = 0.60 (FIR threshold — same as FIR.py)
  
  Each iteration:
    1. SIE: plan queries based on PRIOR iteration's FIR proposals
    2. Sandcrawler: collect evidence for those queries
    3. SEE: derive patch candidates from evidence
    4. Run full MPP on patched task
    5. FIR: measure fitness
    6. If fitness >= COMMIT_THRESHOLD → STOP (success)
    7. If delta < IMPROVEMENT_THRESHOLD → STOP (plateau, escalate)
    8. Else → continue with FIR proposals as next iteration's input
    
  Termination invariant (MAX_DEPTH = 3, from RUBRIC_RECURSION_BOUND_RULE):
    If iteration 3 completes without COMMIT → escalate to human.
    Never attempt iteration 4 automatically.
"""
```

**Fitness criteria for MPP stage quality (extends FIR's 4 criteria):**

| Criterion | Weight | Measurement |
|-----------|--------|-------------|
| stage_completion_rate | 0.25 | mandatory stages completed / 5 |
| constraint_coverage | 0.25 | CDR constraints addressed in IMPL / total CDR constraints |
| erac_clean_rate | 0.20 | ERAC-001-004 all pass / total VERIFICATION runs |
| council_quorum_rate | 0.20 | VERIFICATION quorum met / total VERIFICATION runs |
| evidence_anchor_rate | 0.10 | IMPLEMENTATION claims backed by SEE evidence / total claims |

**SIE query generation from FIR proposals:**

```python
def sie_queries_from_proposals(proposals: list) -> list:
    """
    Each FIR PatchProposal has source_criterion and observation.
    Map to targeted SEE queries:
      stage_completion_rate → "MPP {failed_stage} stage implementation pattern"
      constraint_coverage → "CDR constraint coverage implementation technique"  
      erac_clean_rate → "ERAC {failed_code} detection and prevention"
      council_quorum_rate → "council vote quorum verification governance"
    """
```

---

## PHASE 4 — TESTS (MANDATORY BEFORE SHIPPING)

Write `tests/test_mpp_full_pipeline.py`:

```python
"""
Tests that must ALL pass before this bundle ships.
Run with: PYTHONPATH=engines python3 tests/test_mpp_full_pipeline.py
"""

def test_see_fails_without_runner():
    # SEE raises RuntimeError when no host runner injected
    
def test_cdr_rejects_empty_constraints():
    # CDR raises CDRViolation when output has no constraints
    
def test_cdr_rejects_vague_constraints():
    # CDR raises CDRViolation for constraints containing "good" or "clean"
    
def test_implementation_uses_guarded_write():
    # No raw file writes — all artifacts go through guarded_write
    
def test_verification_requires_all_4_councils():
    # VERIFICATION with missing council → FAIL
    
def test_verification_quorum_below_85_fails():
    # council votes: RATIONALITY=4, RELIABILITY=2, ETHICS=2, BUILDER=2 → FAIL
    
def test_ecl_blocked_when_verification_failed():
    # ECL never runs if VERIFICATION verdict != PASS
    
def test_ecl_blocked_when_fir_insufficient_data():
    # ECL returns BLOCKED not LOCKED when FIR has no BTS log
    
def test_full_pipeline_passes_good_task():
    # Full SEE→CDR→IMPL→VERIF→ECL run with injected mock runner
    # Must return ecl_status="LOCKED" and session_committed=True
    
def test_improvement_loop_stops_at_max_3():
    # Loop never exceeds 3 iterations regardless of fitness
    
def test_improvement_loop_commits_above_threshold():
    # When FIR score >= 0.60, loop stops and returns COMMITTED
```

---

## RECEIPTS TO PRODUCE

Every phase must produce a receipt before the next phase begins:

1. `receipts/MPP_BUILD_RESEARCH_RECEIPT.json` — after Phase 0
2. `receipts/CDR_STAGE_ENGINE_RECEIPT.json` — after CDR implementation + test pass
3. `receipts/IMPLEMENTATION_STAGE_ENGINE_RECEIPT.json` — after IMPL + test pass
4. `receipts/VERIFICATION_STAGE_ENGINE_RECEIPT.json` — after VERIF + test pass
5. `receipts/ECL_STAGE_ENGINE_RECEIPT.json` — after ECL + FIR wire + test pass
6. `receipts/MPP_WIRING_RECEIPT.json` — after MPP_RUNTIME dispatch updated
7. `receipts/IMPROVEMENT_LOOP_RECEIPT.json` — after loop + termination tests pass
8. `receipts/MPP_FULL_PIPELINE_RECEIPT.json` — after ALL tests pass end-to-end

Each receipt must contain: `stage`, `timestamp_utc`, `tests_passed`, `tests_run`, `artifact_hashes`, `sha256_of_this_receipt`.

---

## HARD INVARIANTS — NEVER VIOLATE

1. **No fabricated outputs.** Every stage must return data derived from actual execution. No hardcoded `{"ok": True}`.

2. **No raw file writes.** All artifact writes go through `guarded_write` or `VERIFIED_WRITE_v3`.

3. **SEE before CDR before IMPLEMENTATION before VERIFICATION before ECL.** Order violations raise `MPPViolationError`.

4. **ECL never skips FIR.** If FIR cannot run, ECL returns BLOCKED. It never returns LOCKED without a FIR result.

5. **Improvement loop max depth 3.** After 3 iterations without commit, escalate. Never iterate 4.

6. **Tests must pass before receipts.** No receipt may be written for a phase whose tests have not all passed.

7. **Fail closed.** When in doubt, raise. Never return a passing result to avoid an error.

---

## WHAT SUCCESS LOOKS LIKE

```python
# This must work end-to-end after your build:
from GLOBAL_EXECUTION_GATE import GlobalExecutionGate
GlobalExecutionGate.enter_pipeline()

from HOST_WEB_RUNNER_BRIDGE import set_host_web_runner
set_host_web_runner(your_web_search_function)

from MPP_IMPROVEMENT_LOOP import run_improvement_loop

result = run_improvement_loop(
    task={
        "type": "lesson_plan",
        "description": "3rd grade bilingual TEKS 3.6C science lesson on photosynthesis",
        "see_query": "TEKS 3.6C photosynthesis bilingual emergent bilingual scaffolding"
    },
    runtime_root="/path/to/Metablooms_OS"
)

assert result["status"] in ("COMMITTED", "ESCALATED")
assert result["iterations"] <= 3
assert result["fir_score"] >= 0.0
assert len(result["receipts"]) == result["iterations"]
```
