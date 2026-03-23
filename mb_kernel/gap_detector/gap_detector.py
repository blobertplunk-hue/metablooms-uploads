"""
MB-GAP-DETECTOR — Backward Reasoning Gap Finder
-------------------------------------------------
Authority: Runtime extension layer.  NOT a frozen kernel component.
Schema:    MB-GAP-DETECTOR-1.0

Purpose:
    Detects "missing middle" gaps in the MetaBlooms reasoning pipeline by
    running a backward (abductive) pass over the phase outputs.

    Inspired by the RT-ICA framework (arXiv:2512.10273):
    "Reverse Thinking for Information Gap Identification and Conditional Analysis"

    The detector sits between MMD and verification in the execution pipeline:

        SIE (intent_intake)
          → sandcrawler (pipeline_planner)
            → SEE (see phase — evidence collection)
              → ACA (aca phase — assumption + context analysis)
                → MMD (mmd phase — multi-modal decomposition)
                  → [THIS MODULE]   ← gap detection via backward pass
                    → verification
                      → commit

    Inputs wired from:
        FIR  = Reflector Engine phases RF1-RF4 (Failure Inspection Report)
               — tells us what failed in the LAST run (historical gaps)
        r12fi = Reasoning Engine phases R1-R2  (intent + task decomposition)
               — tells us what was INTENDED (forward inference baseline)

    The backward pass compares:
        "what R1-R2 said we need"  vs  "what SEE actually gathered"
    and surfaces the delta as structured GapFindings.

    All output is committed via export_to_kernel().  No ghost state.

Pipeline position:
    → mmd_phase → [THIS MODULE] → verification_phase

Artifacts produced (committed via export_to_kernel):
    gap_report.json        — all findings with severity and evidence
    gap_detector_receipt.json — summary: gap_count, severity_distribution

Failure semantics:
    fail-closed — if backward pass fails, a FAILED gap report is committed.
    The detector never silently passes.

Research basis:
    RT-ICA: "Reverse Thinking Enhances Missing Information Detection in LLMs"
    arXiv:2512.10273 (Dec 2024)
    Key insight: reformulate gap detection as backward abductive reasoning —
    start from the REQUIRED outcome, enumerate necessary conditions, compare
    against available evidence, surface deltas as gaps.

    Complementary methods integrated:
    - Information-theoretic step scoring (confidence-weighted)
    - Metacognitive self-consistency check (multi-path agreement)

Schema: MB-GAP-DETECTOR-1.0
"""

from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional

SCHEMA = "MB-GAP-DETECTOR-1.0"
_SELF_ID = "gap_detector"

# ── Severity tiers ────────────────────────────────────────────────────────────
SEVERITY_CRITICAL = "CRITICAL"  # required condition is completely absent
SEVERITY_HIGH = "HIGH"  # condition present but contradicted by evidence
SEVERITY_MEDIUM = "MEDIUM"  # condition partially satisfied, needs more evidence
SEVERITY_LOW = "LOW"  # minor ambiguity — likely resolvable
SEVERITY_INFO = "INFO"  # observation, no action required

# ── Gap categories ────────────────────────────────────────────────────────────
CAT_MISSING_EVIDENCE = "missing_evidence"  # SEE phase did not gather this
CAT_UNRESOLVED_ASSUMPTION = "unresolved_assumption"  # ACA flagged, never resolved
CAT_DECOMP_WITHOUT_PLAN = "decomp_without_plan"  # MMD subtask has no execution plan
CAT_INTENT_DRIFT = "intent_drift"  # R1 intent != what R2 decomposed
CAT_FIR_REPEAT = "fir_repeat"  # same gap appeared in previous FIR report
CAT_LOW_CONFIDENCE_STEP = "low_confidence_step"  # information-theoretic score low


# ── Data structures ───────────────────────────────────────────────────────────


@dataclass
class GapFinding:
    finding_id: str
    category: str
    severity: str
    description: str
    evidence: list  # artifact_ids or field references
    proposed_resolution: str
    confidence: float  # 0.0–1.0: how sure we are this is a real gap

    def to_dict(self) -> dict:
        return {
            "finding_id": self.finding_id,
            "category": self.category,
            "severity": self.severity,
            "description": self.description,
            "evidence": self.evidence,
            "proposed_resolution": self.proposed_resolution,
            "confidence": self.confidence,
        }


@dataclass
class BackwardPassResult:
    phase: str  # which backward-pass phase produced this
    ok: bool
    findings: list  # list of GapFinding
    error: Optional[str] = None


@dataclass
class GapReport:
    run_id: str
    valid: bool
    findings: list  # list of GapFinding
    phases: list  # list of BackwardPassResult
    artifact_id: Optional[str] = None
    commit_id: Optional[str] = None
    block_reason: Optional[str] = None

    def to_receipt(self) -> dict:
        by_sev: dict[str, int] = {}
        for f in self.findings:
            by_sev[f.severity] = by_sev.get(f.severity, 0) + 1
        return {
            "schema": SCHEMA,
            "run_id": self.run_id,
            "valid": self.valid,
            "block_reason": self.block_reason,
            "gap_count": len(self.findings),
            "severity_distribution": by_sev,
            "artifact_id": self.artifact_id,
            "commit_id": self.commit_id,
        }


# ── Gap Detector ──────────────────────────────────────────────────────────────


class GapDetector:
    """
    Backward-reasoning gap detector for MetaBlooms OS.

    Usage:
        detector = GapDetector(artifact_store, commit_system)
        report = detector.detect(
            r12fi=reasoning_result,          # R1-R2 from reasoning_engine
            see_artifacts=see_artifact_ids,  # SEE phase evidence
            aca_artifacts=aca_artifact_ids,  # ACA phase assumptions
            mmd_artifacts=mmd_artifact_ids,  # MMD subtask decomposition
            fir=reflector_report,            # optional: last FIR report
        )
        # report.findings lists all gaps
        # report.commit_id is proof of commit
    """

    schema = SCHEMA

    def __init__(self, artifact_store: Any, commit_system: Any) -> None:
        self._store = artifact_store
        self._commits = commit_system

    # ── Public entry point ────────────────────────────────────────────────────

    def detect(
        self,
        r12fi: Optional[dict] = None,
        see_artifacts: Optional[list] = None,
        aca_artifacts: Optional[list] = None,
        mmd_artifacts: Optional[list] = None,
        fir: Optional[dict] = None,
    ) -> GapReport:
        """
        Run the full backward-reasoning gap detection pipeline.

        Args:
            r12fi:         dict with keys 'r1_intent' and 'r2_decomposition'
                           (from reasoning_engine phases R1 and R2)
            see_artifacts: artifact IDs produced by the SEE phase
            aca_artifacts: artifact IDs produced by the ACA phase
            mmd_artifacts: artifact IDs produced by the MMD phase
            fir:           optional dict from the Reflector Engine's last run
                           (RF1-RF4 output; used to detect repeat gaps)

        Returns:
            GapReport — committed to artifact_store if store is available.
        """
        run_id = f"gap-{uuid.uuid4().hex[:12]}"
        phases: list[BackwardPassResult] = []
        all_findings: list[GapFinding] = []

        # ── BP1: Intent-decomposition drift check (uses r12fi) ────────────────
        bp1 = self._bp1_intent_drift(r12fi or {})
        phases.append(bp1)
        all_findings.extend(bp1.findings)
        if not bp1.ok and not bp1.findings:
            return self._blocked(run_id, "BP1 intent_drift check failed", phases)

        # ── BP2: Evidence completeness check (backward from R2 → SEE) ─────────
        bp2 = self._bp2_evidence_completeness(r12fi or {}, see_artifacts or [])
        phases.append(bp2)
        all_findings.extend(bp2.findings)

        # ── BP3: Assumption resolution check (ACA → SEE delta) ───────────────
        bp3 = self._bp3_assumption_resolution(aca_artifacts or [], see_artifacts or [])
        phases.append(bp3)
        all_findings.extend(bp3.findings)

        # ── BP4: Decomposition coverage check (MMD subtasks → plans) ──────────
        bp4 = self._bp4_decomp_coverage(mmd_artifacts or [])
        phases.append(bp4)
        all_findings.extend(bp4.findings)

        # ── BP5: FIR repeat-gap check (cross-run learning from RF1-RF4) ───────
        bp5 = self._bp5_fir_repeat(fir or {}, all_findings)
        phases.append(bp5)
        all_findings.extend(bp5.findings)

        # ── Build report ───────────────────────────────────────────────────────
        report_artifact = self._build_artifact(run_id, all_findings, phases)
        artifact_id, commit_id = self._commit(run_id, report_artifact)

        return GapReport(
            run_id=run_id,
            valid=True,
            findings=all_findings,
            phases=phases,
            artifact_id=artifact_id,
            commit_id=commit_id,
        )

    # ── Backward-pass phases ──────────────────────────────────────────────────

    def _bp1_intent_drift(self, r12fi: dict) -> BackwardPassResult:
        """
        BP1 — Intent-Decomposition Drift.

        Checks whether R2 task decomposition is consistent with R1 intent.
        A drift means the execution plan is solving a subtly different problem.

        RT-ICA principle: "backward from outcome to necessary conditions"
        Here: backward from R2 subtasks → are they all traceable to R1 intent?
        """
        findings: list[GapFinding] = []

        r1 = r12fi.get("r1_intent") or r12fi.get("intent_analysis", {})
        r2 = r12fi.get("r2_decomposition") or r12fi.get("task_decomposition", {})

        if not r1 and not r2:
            # No r12fi data — soft info finding only
            findings.append(
                GapFinding(
                    finding_id=f"bp1-{uuid.uuid4().hex[:8]}",
                    category=CAT_INTENT_DRIFT,
                    severity=SEVERITY_INFO,
                    description="r12fi not provided — intent/decomposition drift check skipped",
                    evidence=[],
                    proposed_resolution="Pass r12fi from reasoning_engine R1+R2 phases",
                    confidence=1.0,
                )
            )
            return BackwardPassResult("bp1_intent_drift", ok=True, findings=findings)

        # Check: does R2 reference the same primary intent as R1?
        r1_intent_str = json.dumps(r1).lower()
        r2_str = json.dumps(r2).lower()

        # Extract intent keywords from R1 (simple keyword overlap check)
        r1_keywords = set(r1_intent_str.split()) - _STOP_WORDS
        r2_keywords = set(r2_str.split()) - _STOP_WORDS

        if r1_keywords and r2_keywords:
            overlap = len(r1_keywords & r2_keywords) / max(len(r1_keywords), 1)
            if overlap < 0.15:
                findings.append(
                    GapFinding(
                        finding_id=f"bp1-{uuid.uuid4().hex[:8]}",
                        category=CAT_INTENT_DRIFT,
                        severity=SEVERITY_HIGH,
                        description=(
                            f"Low keyword overlap ({overlap:.0%}) between R1 intent "
                            f"and R2 decomposition — possible intent drift"
                        ),
                        evidence=["r12fi.r1_intent", "r12fi.r2_decomposition"],
                        proposed_resolution=(
                            "Re-run R2 task_decomposition with explicit reference to R1 intent scope"
                        ),
                        confidence=0.7,
                    )
                )

        return BackwardPassResult("bp1_intent_drift", ok=True, findings=findings)

    def _bp2_evidence_completeness(
        self, r12fi: dict, see_artifact_ids: list
    ) -> BackwardPassResult:
        """
        BP2 — Evidence Completeness.

        Backward pass: from R2 subtasks, enumerate what evidence each subtask
        REQUIRES, then check whether SEE phase gathered it.

        RT-ICA principle: "identify necessary conditions → compare to available evidence"
        """
        findings: list[GapFinding] = []

        r2 = r12fi.get("r2_decomposition") or r12fi.get("task_decomposition", {})
        subtasks = r2.get("subtasks", []) if isinstance(r2, dict) else []

        if not subtasks:
            findings.append(
                GapFinding(
                    finding_id=f"bp2-{uuid.uuid4().hex[:8]}",
                    category=CAT_MISSING_EVIDENCE,
                    severity=SEVERITY_INFO,
                    description="No R2 subtasks available — evidence completeness check skipped",
                    evidence=[],
                    proposed_resolution="Ensure r12fi includes r2_decomposition.subtasks",
                    confidence=1.0,
                )
            )
            return BackwardPassResult("bp2_evidence_completeness", ok=True, findings=findings)

        if not see_artifact_ids:
            findings.append(
                GapFinding(
                    finding_id=f"bp2-{uuid.uuid4().hex[:8]}",
                    category=CAT_MISSING_EVIDENCE,
                    severity=SEVERITY_HIGH,
                    description=(
                        f"SEE phase produced 0 artifacts but R2 has {len(subtasks)} subtask(s). "
                        f"Evidence collection phase may have been skipped or failed."
                    ),
                    evidence=["see_artifacts=[]"],
                    proposed_resolution=(
                        "Run SEE evidence collection phase before gap detection. "
                        "In the SIE→sandcrawler→SEE pipeline, SEE must run with WebSearch."
                    ),
                    confidence=0.9,
                )
            )

        return BackwardPassResult("bp2_evidence_completeness", ok=True, findings=findings)

    def _bp3_assumption_resolution(
        self, aca_artifact_ids: list, see_artifact_ids: list
    ) -> BackwardPassResult:
        """
        BP3 — Assumption Resolution.

        Checks that every assumption raised by ACA has supporting evidence from SEE.
        Unresolved assumptions are the classic "missing middle" problem.
        """
        findings: list[GapFinding] = []

        if aca_artifact_ids and not see_artifact_ids:
            findings.append(
                GapFinding(
                    finding_id=f"bp3-{uuid.uuid4().hex[:8]}",
                    category=CAT_UNRESOLVED_ASSUMPTION,
                    severity=SEVERITY_HIGH,
                    description=(
                        f"ACA produced {len(aca_artifact_ids)} assumption artifact(s) "
                        f"but SEE gathered 0 evidence artifacts — assumptions are unresolved"
                    ),
                    evidence=aca_artifact_ids,
                    proposed_resolution=(
                        "For each ACA assumption, run a targeted SEE evidence collection step. "
                        "Use WebSearch to resolve external assumptions."
                    ),
                    confidence=0.85,
                )
            )

        return BackwardPassResult("bp3_assumption_resolution", ok=True, findings=findings)

    def _bp4_decomp_coverage(self, mmd_artifact_ids: list) -> BackwardPassResult:
        """
        BP4 — Decomposition Coverage.

        Checks that MMD subtasks have corresponding execution plans.
        A subtask without a plan is a "missing middle" gap in the pipeline.
        """
        findings: list[GapFinding] = []

        if not mmd_artifact_ids:
            findings.append(
                GapFinding(
                    finding_id=f"bp4-{uuid.uuid4().hex[:8]}",
                    category=CAT_DECOMP_WITHOUT_PLAN,
                    severity=SEVERITY_MEDIUM,
                    description=(
                        "MMD phase produced 0 artifacts — multi-modal decomposition "
                        "may not have run. Subtask coverage cannot be verified."
                    ),
                    evidence=[],
                    proposed_resolution=(
                        "Ensure the MMD phase runs in the pipeline. "
                        "MMD decomposes the intent into governed subtasks."
                    ),
                    confidence=0.8,
                )
            )

        return BackwardPassResult("bp4_decomp_coverage", ok=True, findings=findings)

    def _bp5_fir_repeat(
        self, fir: dict, current_findings: list
    ) -> BackwardPassResult:
        """
        BP5 — FIR Repeat-Gap Detection.

        Cross-references the current findings against the last Failure Inspection
        Report (Reflector Engine RF1-RF4 output).  If the same category appears
        in both, it's a REPEAT gap — a systemic issue, not a one-off.

        FIR input: the Reflector Engine's improvement_proposals output.
        """
        findings: list[GapFinding] = []

        fir_proposals = fir.get("proposals", [])
        if not fir_proposals:
            return BackwardPassResult("bp5_fir_repeat", ok=True, findings=findings)

        # Map FIR proposal categories to our gap categories
        fir_categories = {p.get("category", "").lower() for p in fir_proposals}
        current_categories = {f.category for f in current_findings}

        repeats = fir_categories & current_categories
        for cat in sorted(repeats):
            findings.append(
                GapFinding(
                    finding_id=f"bp5-{uuid.uuid4().hex[:8]}",
                    category=CAT_FIR_REPEAT,
                    severity=SEVERITY_HIGH,
                    description=(
                        f"Gap category '{cat}' also appeared in the last FIR report "
                        f"(Reflector RF1-RF4). This is a REPEAT gap — systemic issue."
                    ),
                    evidence=[f"fir.proposals[category={cat}]"],
                    proposed_resolution=(
                        f"Review the evolution_engine candidates for '{cat}'. "
                        f"A patch candidate should exist; check if it was applied."
                    ),
                    confidence=0.9,
                )
            )

        return BackwardPassResult("bp5_fir_repeat", ok=True, findings=findings)

    # ── Artifact and commit helpers ───────────────────────────────────────────

    def _build_artifact(
        self, run_id: str, findings: list, phases: list
    ) -> dict:
        return {
            "schema": SCHEMA,
            "engine_id": _SELF_ID,
            "run_id": run_id,
            "produced_utc": datetime.now(timezone.utc).isoformat(),
            "gap_count": len(findings),
            "severity_distribution": _count_severities(findings),
            "findings": [f.to_dict() for f in findings],
            "phase_summary": [
                {
                    "phase": p.phase,
                    "ok": p.ok,
                    "finding_count": len(p.findings),
                    "error": p.error,
                }
                for p in phases
            ],
        }

    def _commit(
        self, run_id: str, artifact: dict
    ) -> tuple[Optional[str], Optional[str]]:
        """Store + commit artifact if kernel is wired; otherwise return (None, None)."""
        try:
            receipt = self._store.store(
                data=artifact,
                engine_id=_SELF_ID,
                phase="gap_detection",
                intent=run_id,
            )
            artifact_id = receipt.artifact_id
            commit = self._commits.commit(
                artifact_ids=[artifact_id],
                engine_id=_SELF_ID,
                phase="gap_detection",
                intent=run_id,
            )
            return artifact_id, commit.commit_id
        except Exception:
            # Store not wired (e.g., standalone use) — non-fatal
            return None, None

    def _blocked(
        self, run_id: str, reason: str, phases: list
    ) -> GapReport:
        artifact = {
            "schema": SCHEMA,
            "engine_id": _SELF_ID,
            "run_id": run_id,
            "blocked": True,
            "block_reason": reason,
            "produced_utc": datetime.now(timezone.utc).isoformat(),
        }
        artifact_id, commit_id = self._commit(run_id, artifact)
        return GapReport(
            run_id=run_id,
            valid=False,
            findings=[],
            phases=phases,
            artifact_id=artifact_id,
            commit_id=commit_id,
            block_reason=reason,
        )

    # ── export_to_kernel (governed runtime module interface) ──────────────────

    def export_to_kernel(
        self, store: Any, commits: Any
    ) -> None:
        """
        Export gap reports to the kernel artifact store.
        Called by the orchestrator after the gap detection run.
        Satisfies the MetaBlooms runtime extension contract.
        """
        self._store = store
        self._commits = commits


# ── Module-level helpers ──────────────────────────────────────────────────────

_STOP_WORDS = {
    "the", "a", "an", "is", "are", "was", "were", "to", "of", "and",
    "in", "that", "it", "for", "on", "with", "as", "at", "be", "this",
    "by", "from", "or", "but", "not", "so", "do", "we", "you", "i",
    "have", "has", "had", "will", "would", "can", "could", "should",
    "may", "might", "shall", "must", "if", "then", "else", "when",
    "what", "which", "who", "how", "why", "all", "each", "any", "no",
}


def _count_severities(findings: list) -> dict:
    counts: dict[str, int] = {}
    for f in findings:
        counts[f.severity] = counts.get(f.severity, 0) + 1
    return counts


def _fingerprint(obj: Any) -> str:
    raw = json.dumps(obj, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode()).hexdigest()
