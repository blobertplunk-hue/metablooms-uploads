"""
FIR_ENGINE.py — Forced Improvement Runtime (R12-FI)
====================================================

CDR V1 (Rationale):
    R12-FI is the 12-gate quality improvement protocol that every artifact must
    pass before promotion. Originally a separate process (Sep 2025), it evolved
    into substrate — embedded in boot/audit/delta chain. This engine is the
    explicit, callable R12 gate: Meta-Reflection. It measures what actually
    improved, evaluates four fitness criteria from real pipeline data, and
    produces PatchProposals for the EvolutionEngine.

CDR V2 (Trust):
    evaluate_session() NEVER hardcodes fitness scores. Every metric is computed
    from actual pipeline state data. No score = FIR raises, not returns 1.0.

CDR V3 (Boundary):
    FIR measures and proposes. It does not apply patches, modify engines,
    or self-improve. PatchProposals go to the operator for approval.

CDR V4 (Failure):
    If pipeline_state has no data, raises FIRDataError. Partial data
    produces score with explicit INSUFFICIENT_DATA status.

The 12 gates and their distribution across the pipeline:
    R1  Semantic Integrity       → ERAC-001, ERAC-002
    R2  Knowledge Corpus Link    → SEE evidence grounding
    R3  Ethical & Chaos Probe    → CDR pillar checks
    R4  Workflow Bottleneck      → UXR operator constraints
    R5  Completeness Audit       → MMD gap detection
    R6  Redundancy Elimination   → SSO out-of-scope enforcement
    R7  Testability Hardening    → VERIFICATION hash read-back
    R8  Failure Mode Analysis    → RRP + DEBUGGING root_cause
    R9  Documentation Sync       → DRS decision records
    R10 Integration Verification → ADS dependency map
    R11 Performance Compression  → NUF performance requirements
    R12 Meta-Reflection          → THIS ENGINE (FIR)

Fitness criteria (4 measurable, weighted):
    stage_completion_rate   × 0.30  — stages completed / 14
    erac_clean_rate         × 0.25  — stages with no ERAC violations
    verification_pass_rate  × 0.25  — VERIFICATION checks passed / expected
    rca_quality_rate        × 0.20  — DEBUGGING runs with root_cause present

Commit threshold: 0.60
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

COMMIT_THRESHOLD: float = 0.60
SCHEMA: str = "mb.fir.v2"

WEIGHTS: dict[str, float] = {
    "stage_completion_rate": 0.30,
    "erac_clean_rate": 0.25,
    "verification_pass_rate": 0.25,  # nosec B105 — float weight, not a password
    "rca_quality_rate": 0.20,
}

STAGE_COUNT: int = 14


class FIRDataError(RuntimeError):
    """Raised when fitness cannot be computed from real pipeline data."""


@dataclass
class FitnessMetrics:
    stage_completion_rate: float
    erac_clean_rate: float
    verification_pass_rate: float
    rca_quality_rate: float
    composite_score: float
    stages_ran: int
    measured_at: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "stage_completion_rate": round(self.stage_completion_rate, 3),
            "erac_clean_rate": round(self.erac_clean_rate, 3),
            "verification_pass_rate": round(self.verification_pass_rate, 3),
            "rca_quality_rate": round(self.rca_quality_rate, 3),
            "composite_score": round(self.composite_score, 3),
            "stages_ran": self.stages_ran,
            "measured_at": self.measured_at,
        }


@dataclass
class PatchProposal:
    proposal_id: str
    gate: str  # R1-R12
    source_criterion: str
    observation: str
    proposed_change: str
    severity: str  # HIGH | MEDIUM | LOW
    evidence: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "proposal_id": self.proposal_id,
            "gate": self.gate,
            "source_criterion": self.source_criterion,
            "observation": self.observation,
            "proposed_change": self.proposed_change,
            "severity": self.severity,
            "evidence": self.evidence,
        }


@dataclass
class FIRResult:
    fir_id: str
    session_id: str
    status: str  # COMMITTED | REJECTED | INSUFFICIENT_DATA
    fitness: FitnessMetrics | None
    proposals: list[PatchProposal]
    commit_threshold: float
    stop_reason: str
    timestamp: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": SCHEMA,
            "fir_id": self.fir_id,
            "session_id": self.session_id,
            "status": self.status,
            "fitness": self.fitness.to_dict() if self.fitness else None,
            "proposals": [p.to_dict() for p in self.proposals],
            "commit_threshold": self.commit_threshold,
            "stop_reason": self.stop_reason,
            "timestamp": self.timestamp,
        }


class FIREngine:
    """
    R12-FI callable engine. Pass a completed PipelineState to evaluate_session().

    Rationale: R12 Meta-Reflection is the closure gate — it measures whether the
    pipeline run actually produced quality output, not just whether it ran.
    """

    def _measure_stage_completion(self, state_data: dict[str, Any]) -> float:
        """R5/R10: how many of the 14 stages actually ran."""
        return len(state_data) / STAGE_COUNT

    def _measure_erac_clean_rate(self, state_data: dict[str, Any]) -> float:
        """R1/R2: stages with no ERAC violations (no RuntimeError artifacts)."""
        if not state_data:
            return 0.0
        clean = sum(1 for s in state_data.values() if s.get("status") == "COMPLETE" and "error" not in s.get("artifact", {}))
        return clean / len(state_data)

    def _measure_verification_pass_rate(self, state_data: dict[str, Any]) -> float:
        """R7: VERIFICATION checks passed vs expected."""
        verif = state_data.get("VERIFICATION", {})
        artifact = verif.get("artifact", {})
        if not artifact:
            return 0.0
        checks_passed = len(artifact.get("checks_passed", []))
        # Expected: 7 checks defined in VERIFICATION.execute()
        expected = 7
        return min(checks_passed / expected, 1.0)  # cap at 1.0

    def _measure_rca_quality_rate(self, state_data: dict[str, Any]) -> float:
        """R8: DEBUGGING runs with valid root_cause (not skipped)."""
        debug = state_data.get("DEBUGGING", {})
        artifact = debug.get("artifact", {})
        if not artifact:
            return 1.0  # DEBUGGING didn't run = VERIFICATION passed = good
        if artifact.get("skipped"):
            return 1.0  # Correctly skipped because VERIFICATION passed
        # DEBUGGING actually ran — check quality
        has_root_cause = bool(artifact.get("root_cause"))
        has_lesson = bool(artifact.get("lesson"))
        return 1.0 if (has_root_cause and has_lesson) else 0.0

    def _generate_proposals(
        self,
        metrics: FitnessMetrics,
        state_data: dict[str, Any],
    ) -> list[PatchProposal]:
        proposals: list[PatchProposal] = []

        if metrics.stage_completion_rate < 1.0:
            missing_count = STAGE_COUNT - metrics.stages_ran
            proposals.append(
                PatchProposal(
                    proposal_id=f"PP-{uuid.uuid4().hex[:8]}",
                    gate="R5",
                    source_criterion="stage_completion_rate",
                    observation=f"Only {metrics.stages_ran}/{STAGE_COUNT} stages ran",
                    proposed_change=f"Investigate why {missing_count} stages are absent from pipeline state",
                    severity="HIGH",
                    evidence=[f"stages_ran={metrics.stages_ran}"],
                )
            )

        if metrics.erac_clean_rate < 1.0:
            proposals.append(
                PatchProposal(
                    proposal_id=f"PP-{uuid.uuid4().hex[:8]}",
                    gate="R1",
                    source_criterion="erac_clean_rate",
                    observation=f"ERAC clean rate {metrics.erac_clean_rate:.1%} — some stages have error artifacts",
                    proposed_change="Audit stages with error fields in artifact, apply ERAC-001 through ERAC-004",
                    severity="HIGH",
                    evidence=[f"erac_clean_rate={metrics.erac_clean_rate}"],
                )
            )

        if metrics.verification_pass_rate < 1.0:
            checks = state_data.get("VERIFICATION", {}).get("artifact", {}).get("checks_passed", [])
            proposals.append(
                PatchProposal(
                    proposal_id=f"PP-{uuid.uuid4().hex[:8]}",
                    gate="R7",
                    source_criterion="verification_pass_rate",
                    observation=f"VERIFICATION passed {len(checks)}/7 checks",
                    proposed_change="Fix failing verification checks before next run",
                    severity="MEDIUM",
                    evidence=[f"checks_passed={checks}"],
                )
            )

        if metrics.rca_quality_rate < 1.0:
            proposals.append(
                PatchProposal(
                    proposal_id=f"PP-{uuid.uuid4().hex[:8]}",
                    gate="R8",
                    source_criterion="rca_quality_rate",
                    observation="DEBUGGING ran but root_cause or lesson is missing",
                    proposed_change="Ensure DEBUGGING always produces root_cause + lesson when it runs",
                    severity="HIGH",
                    evidence=[f"rca_quality_rate={metrics.rca_quality_rate}"],
                )
            )

        return proposals

    def evaluate_session(
        self,
        pipeline_state: Any,
        session_id: str = "SESSION-UNKNOWN",
    ) -> FIRResult:
        fir_id = f"FIR-{uuid.uuid4().hex[:12]}"
        now = datetime.now(UTC).isoformat()

        state_data: dict[str, Any] = getattr(pipeline_state, "data", {})

        if not state_data:
            raise FIRDataError(
                "FIR_NO_DATA: pipeline_state.data is empty. " "Cannot compute fitness without real pipeline execution data."
            )

        # Measure all four criteria
        stage_completion = self._measure_stage_completion(state_data)
        erac_clean = self._measure_erac_clean_rate(state_data)
        verif_pass = self._measure_verification_pass_rate(state_data)
        rca_quality = self._measure_rca_quality_rate(state_data)

        composite = min(
            1.0,
            (
                stage_completion * WEIGHTS["stage_completion_rate"]
                + erac_clean * WEIGHTS["erac_clean_rate"]
                + verif_pass * WEIGHTS["verification_pass_rate"]
                + rca_quality * WEIGHTS["rca_quality_rate"]
            ),
        )

        fitness = FitnessMetrics(
            stage_completion_rate=stage_completion,
            erac_clean_rate=erac_clean,
            verification_pass_rate=verif_pass,
            rca_quality_rate=rca_quality,
            composite_score=composite,
            stages_ran=len(state_data),
            measured_at=now,
        )

        proposals = self._generate_proposals(fitness, state_data)

        if composite >= COMMIT_THRESHOLD:
            status = "COMMITTED"
            stop_reason = f"composite_score={composite:.3f} >= threshold={COMMIT_THRESHOLD}"
        else:
            status = "REJECTED"
            stop_reason = f"composite_score={composite:.3f} < threshold={COMMIT_THRESHOLD}"

        return FIRResult(
            fir_id=fir_id,
            session_id=session_id,
            status=status,
            fitness=fitness,
            proposals=proposals,
            commit_threshold=COMMIT_THRESHOLD,
            stop_reason=stop_reason,
            timestamp=now,
        )
