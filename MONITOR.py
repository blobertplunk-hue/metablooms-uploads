"""
MONITOR.py — Post-execution monitoring and feedback loop (CI/CD model)
=======================================================================

CDR V1 (Rationale):
    The pipeline currently ends at ECL. CI/CD systems continue with Monitor →
    Feedback → Re-queue. Without this, the pipeline has no lifecycle — it runs,
    produces output, and stops. There is no signal about whether the output
    achieved its objective in the real world, no feedback into the improvement
    loop, and no re-queue mechanism for failed objectives. This stage closes that
    gap, transforming MPP from a one-shot pipeline into a lifecycle system.

CDR V2 (Trust):
    MONITOR observes — it reads pipeline outputs and prior stage data.
    It does not modify prior stage results or re-run stages. Feedback signals
    are recommendations, not automatic actions. Re-queue decisions require
    operator approval (Robert).

CDR V3 (Boundary):
    Inputs:  full PipelineState (all prior stage data + trace)
    Outputs: MonitorReport with health score, signals, feedback, requeue_recommended
    Side effects: none — MONITOR is read-only
    Assumptions: runs after ECL, has access to complete pipeline state

CDR V4 (Failure):
    If pipeline state is empty → block. Cannot monitor what was not executed.
    Degraded health → warning, not block. Requeue recommendation requires operator.

Integration contract:
    Inputs:  state.data (all stage artifacts), state.trace, FIR result if available
    Outputs: {'health_score', 'signals', 'feedback', 'requeue_recommended', 'requeue_reason'}
    Side effects: none
    Assumptions: ECL has run and confirmed pipeline_complete=True
"""

from __future__ import annotations

from typing import Any

from STAGE_BASE import StageBase

HEALTH_THRESHOLDS: dict[str, float] = {
    "critical": 0.50,
    "degraded": 0.75,
    "healthy": 0.90,
}


class MONITOR(StageBase):
    name = "MONITOR"

    def _compute_health_score(self, state_data: dict[str, Any]) -> float:
        """Compute overall pipeline health from stage artifacts."""
        signals: list[float] = []

        # Signal 1: all 14 stages ran
        stage_count = len(state_data)
        signals.append(min(stage_count / 14, 1.0))

        # Signal 2: VERIFICATION check coverage
        verif = state_data.get("VERIFICATION", {}).get("artifact", {})
        checks = len(verif.get("checks_passed", []))
        signals.append(min(checks / 7, 1.0))

        # Signal 3: CDR compliance
        cdr = state_data.get("CDR", {}).get("artifact", {})
        signals.append(1.0 if cdr.get("cdr_compliant") else 0.0)

        # Signal 4: MMD gap count (0 gaps = 1.0, each gap reduces score)
        mmd = state_data.get("MMD", {}).get("artifact", {})
        gap_count = mmd.get("gap_count", 0)
        signals.append(max(0.0, 1.0 - gap_count * 0.1))

        # Signal 5: TRACE_ANALYSIS integrity (if present)
        trace_a = state_data.get("TRACE_ANALYSIS", {}).get("artifact", {})
        if trace_a:
            signals.append(trace_a.get("integrity_score", 1.0))

        return round(sum(signals) / len(signals), 3) if signals else 0.0

    def _generate_feedback(
        self,
        state_data: dict[str, Any],
        health_score: float,
    ) -> list[dict[str, Any]]:
        """Generate actionable feedback signals from pipeline state."""
        feedback: list[dict[str, Any]] = []

        # Feedback: low CDR compliance
        cdr = state_data.get("CDR", {}).get("artifact", {})
        if cdr.get("warning_count", 0) > 0:
            feedback.append(
                {
                    "source": "CDR",
                    "signal": "CDR_WARNINGS",
                    "detail": f"{cdr['warning_count']} CDR warnings — review for improvement",
                    "priority": "LOW",
                    "action": "review CDR pillars with warn-level violations",
                }
            )

        # Feedback: MMD gaps detected (non-critical ones that passed)
        mmd = state_data.get("MMD", {}).get("artifact", {})
        gaps = mmd.get("gaps", [])
        if gaps:
            feedback.append(
                {
                    "source": "MMD",
                    "signal": "MMD_GAPS_PRESENT",
                    "detail": f"{len(gaps)} non-critical gaps in evidence chain",
                    "priority": "MEDIUM",
                    "action": "address gaps before next pipeline run",
                }
            )

        # Feedback: trace anomalies
        trace_a = state_data.get("TRACE_ANALYSIS", {}).get("artifact", {})
        if trace_a.get("anomaly_count", 0) > 0:
            feedback.append(
                {
                    "source": "TRACE_ANALYSIS",
                    "signal": "TRACE_ANOMALIES",
                    "detail": f"{trace_a['anomaly_count']} trace anomalies detected",
                    "priority": "MEDIUM" if trace_a.get("high_severity_count", 0) == 0 else "HIGH",
                    "action": "investigate anomalous stage artifacts",
                }
            )

        # Feedback: health degraded
        if health_score < HEALTH_THRESHOLDS["degraded"]:
            feedback.append(
                {
                    "source": "MONITOR",
                    "signal": "HEALTH_DEGRADED",
                    "detail": f"Pipeline health score {health_score:.2f} below threshold {HEALTH_THRESHOLDS['degraded']}",
                    "priority": "HIGH",
                    "action": "investigate before re-running pipeline",
                }
            )

        return feedback

    def execute(self, state: Any) -> dict[str, Any]:
        state_data: dict[str, Any] = getattr(state, "data", {})

        if not state_data:
            raise RuntimeError("MONITOR_NO_STATE: state.data is empty — cannot monitor empty pipeline")

        # ECL must have confirmed pipeline_complete
        ecl = state_data.get("ECL", {}).get("artifact", {})
        if not ecl.get("pipeline_complete"):
            raise RuntimeError("MONITOR_PIPELINE_INCOMPLETE: ECL did not confirm pipeline_complete=True")

        health_score = self._compute_health_score(state_data)
        feedback = self._generate_feedback(state_data, health_score)

        # Determine health label
        if health_score >= HEALTH_THRESHOLDS["healthy"]:
            health_label = "HEALTHY"
        elif health_score >= HEALTH_THRESHOLDS["degraded"]:
            health_label = "DEGRADED"
        else:
            health_label = "CRITICAL"

        # Requeue recommendation: only if health is critical
        requeue_recommended = health_label == "CRITICAL"
        requeue_reason = (
            f"health_score={health_score} below critical threshold {HEALTH_THRESHOLDS['critical']}"
            if requeue_recommended
            else "health acceptable"
        )

        high_priority = [f for f in feedback if f["priority"] == "HIGH"]

        return {
            "health_score": health_score,
            "health_label": health_label,
            "signals": [f["signal"] for f in feedback],
            "feedback": feedback,
            "feedback_count": len(feedback),
            "high_priority_count": len(high_priority),
            "requeue_recommended": requeue_recommended,
            "requeue_reason": requeue_reason,
            "lifecycle_complete": True,
        }
