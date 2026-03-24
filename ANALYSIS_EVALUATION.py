"""
ANALYSIS_EVALUATION.py — StageBase wrapper for ANALYSIS_EVALUATION_ENGINE
==========================================================================

CDR V1 (Rationale):
    Thin stage wrapper. All logic is in the engine.
    Reads analysis_text from state.task (preferred) or from TRACE_ANALYSIS
    artifact in state.data (our pipeline's actual state structure).

CDR V2 (Trust):
    Uses state.data not state.outputs — matches PipelineState implementation.
    Returns dict with required keys: stage, status, artifact, trace_span.

CDR V3 (Boundary):
    Inputs:  PipelineState with analysis_text in task OR TRACE_ANALYSIS in data
    Outputs: artifact dict with score, verdict, receipt_path, receipt_hash
    Side effects: writes receipt file via engine
    Assumptions: ANALYSIS_EVALUATION_ENGINE importable from engines/

CDR V4 (Failure):
    Empty analysis_text: engine returns FAIL verdict, stage still completes.
    Engine write failure: RuntimeError propagates, StageRunner blocks pipeline.
    safe_state: never silently pass an analysis that was not evaluated.

CDR V5 (S-tier):
    result_hash on artifact for pipeline integrity (STAGE_BASE injects artifact_hash).
    truth_gate_blocked surfaced in artifact for FIR and MONITOR visibility.
"""

from __future__ import annotations

import sys
import os

# Allow import when running from different working directories
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from engines.ANALYSIS_EVALUATION_ENGINE import evaluate_analysis


class StageBase:
    """Minimal StageBase stub for standalone use. Real import: from STAGE_BASE import StageBase."""

    name = "BASE"

    def run(self, state):  # noqa: ANN001
        artifact = self.execute(state)
        return {
            "stage": self.name,
            "status": "COMPLETE",
            "artifact": artifact,
            "trace_span": {"stage": self.name, "artifacts": artifact},
        }

    def execute(self, state):  # noqa: ANN001
        raise NotImplementedError


try:
    # Use real StageBase when running inside the pipeline
    from STAGE_BASE import StageBase as _RealStageBase  # type: ignore[import]

    _Base = _RealStageBase
except ImportError:
    _Base = StageBase


class ANALYSIS_EVALUATION(_Base):  # type: ignore[valid-type,misc]
    name = "ANALYSIS_EVALUATION"

    def execute(self, state) -> dict:  # noqa: ANN001
        # Prefer explicit analysis_text in task dict
        analysis_text: str = state.task.get("analysis_text", "")

        # Fallback: read from TRACE_ANALYSIS artifact in state.data (our pipeline)
        if not analysis_text:
            trace_art = state.data.get("TRACE_ANALYSIS", {}).get("artifact", {})
            analysis_text = trace_art.get("analysis", "")

        # Build context from pipeline state
        artifact_list: list[str] = []
        for stage_name, stage_result in state.data.items():
            art = stage_result.get("artifact", {})
            path = art.get("artifact_path", "")
            if path:
                artifact_list.append(str(path))

        context = {
            "artifacts": artifact_list,
            "receipts": list(state.data.keys()),  # stage names as receipt anchors
            "invariants": state.task.get("invariants", []),
        }

        result = evaluate_analysis(analysis_text, context)

        return {
            "score": result["score"],
            "truth_gate_blocked": result["truth_gate_blocked"],
            "verdict": result["verdict"],
            "breakdown": result["breakdown"],
            "receipt_path": result["receipt_path"],
            "receipt_hash": result["receipt_hash"],
            "evidence_issues": result["evidence_issues"],
        }
