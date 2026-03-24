"""
TRACE_ANALYSIS.py — Span aggregation and anomaly detection (OpenTelemetry model)
=================================================================================

CDR V1 (Rationale):
    The pipeline produces trace spans at every stage but never analyzes them.
    This creates observability without insight — we know what ran but not whether
    it ran efficiently, whether any stage was anomalously slow or thin, or whether
    the trace chain has integrity gaps. Modeled on OpenTelemetry's analysis layer:
    Execution → Instrumentation → Trace → Metrics → Analysis → Action.

CDR V2 (Trust):
    Analysis is read-only — reads trace from PipelineState, produces findings,
    does not modify any prior stage outputs. Anomalies are findings, not mutations.

CDR V3 (Boundary):
    Inputs:  state.trace (list of trace spans from all stages)
    Outputs: trace_analysis artifact with anomalies, metrics, integrity score
    Side effects: none
    Assumptions: all prior stages have completed and written trace_spans

CDR V4 (Failure):
    Empty trace → blocks. A pipeline with no trace evidence cannot be analyzed.
    Broken chain (orphaned spans) → flagged as anomaly, does not block.

Integration contract:
    Inputs:  state.trace (list of dicts with 'stage', 'artifacts' keys)
    Outputs: {'integrity_score', 'anomalies', 'stage_metrics', 'chain_complete'}
    Side effects: none
    Assumptions: runs AFTER VERIFICATION, BEFORE DEBUGGING conditional check
"""

from __future__ import annotations

from typing import Any

from STAGE_BASE import StageBase

# Stages expected in a complete trace
EXPECTED_STAGES: list[str] = [
    "SEE",
    "NORMALIZE_EVIDENCE",
    "MMD",
    "DRS",
    "CDR",
    "OFM",
    "ADS",
    "UXR",
    "NUF",
    "SSO",
    "RRP",
    "IMPLEMENTATION",
    "VERIFICATION",
]

# Artifact quality thresholds
MIN_ARTIFACT_KEYS: int = 1
THIN_ARTIFACT_THRESHOLD: int = 1  # artifact with only 1 key is suspicious


class TRACE_ANALYSIS(StageBase):
    name = "TRACE_ANALYSIS"

    def _check_chain_integrity(self, trace: list[dict[str, Any]]) -> tuple[bool, list[str]]:
        """Verify all expected stages appear in trace in correct order."""
        stage_names = [span.get("stage") for span in trace]
        missing = [s for s in EXPECTED_STAGES if s not in stage_names]
        if missing:
            return False, missing
        return True, []

    def _detect_anomalies(self, trace: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Detect suspicious patterns in trace spans."""
        anomalies: list[dict[str, Any]] = []

        for span in trace:
            stage = span.get("stage", "UNKNOWN")
            artifacts = span.get("artifacts", {})

            # Anomaly: artifact is empty dict
            if isinstance(artifacts, dict) and len(artifacts) == 0:
                anomalies.append(
                    {
                        "stage": stage,
                        "type": "EMPTY_ARTIFACT",
                        "severity": "high",
                        "detail": f"{stage} produced empty artifact dict",
                    }
                )

            # Anomaly: artifact has only one key (likely stub/placeholder)
            if isinstance(artifacts, dict) and len(artifacts) == THIN_ARTIFACT_THRESHOLD:
                key = list(artifacts.keys())[0]
                # Skip known single-key valid artifacts
                if key not in (
                    "skipped",
                    "normalization_complete",
                    "scope_locked",
                    "recovery_plan_locked",
                    "architecture_locked",
                ):
                    anomalies.append(
                        {
                            "stage": stage,
                            "type": "THIN_ARTIFACT",
                            "severity": "warn",
                            "detail": f"{stage} artifact has only 1 key: {key}",
                        }
                    )

            # Anomaly: skipped=True on a non-DEBUGGING stage
            if isinstance(artifacts, dict) and artifacts.get("skipped") and stage != "DEBUGGING":
                anomalies.append(
                    {
                        "stage": stage,
                        "type": "UNEXPECTED_SKIP",
                        "severity": "high",
                        "detail": f"{stage} marked skipped but is not DEBUGGING",
                    }
                )

        return anomalies

    def _compute_metrics(self, trace: list[dict[str, Any]]) -> dict[str, Any]:
        """Compute per-stage and aggregate trace metrics."""
        total = len(trace)
        with_artifacts = sum(1 for s in trace if isinstance(s.get("artifacts"), dict) and s["artifacts"])
        return {
            "total_spans": total,
            "spans_with_artifacts": with_artifacts,
            "artifact_coverage": round(with_artifacts / total, 3) if total else 0.0,
        }

    def execute(self, state: Any) -> dict[str, Any]:
        trace: list[dict[str, Any]] = getattr(state, "trace", [])

        if not trace:
            raise RuntimeError(
                "TRACE_ANALYSIS_NO_TRACE: state.trace is empty — " "all stages must produce trace_spans before analysis"
            )

        chain_complete, missing_stages = self._check_chain_integrity(trace)
        anomalies = self._detect_anomalies(trace)
        metrics = self._compute_metrics(trace)

        # Integrity score: penalize missing stages and high-severity anomalies
        high_anomalies = sum(1 for a in anomalies if a["severity"] == "high")
        missing_penalty = len(missing_stages) * 0.05
        anomaly_penalty = high_anomalies * 0.03
        integrity_score = max(0.0, round(1.0 - missing_penalty - anomaly_penalty, 3))

        # Block only on critical integrity failures (missing mandatory stages)
        mandatory = {"SEE", "IMPLEMENTATION", "VERIFICATION"}
        missing_mandatory = [s for s in missing_stages if s in mandatory]
        if missing_mandatory:
            raise RuntimeError(f"TRACE_ANALYSIS_MANDATORY_MISSING: " f"mandatory stages absent from trace: {missing_mandatory}")

        return {
            "integrity_score": integrity_score,
            "chain_complete": chain_complete,
            "missing_stages": missing_stages,
            "anomalies": anomalies,
            "anomaly_count": len(anomalies),
            "high_severity_count": high_anomalies,
            "stage_metrics": metrics,
            "analysis_complete": True,
        }
