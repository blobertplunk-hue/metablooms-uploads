"""
MPP_RUNTIME.py — Full lifecycle pipeline (v2 — CI/CD + observability model)
============================================================================

CDR V1 (Rationale):
    v1 ended at ECL. v2 extends to full lifecycle: SEE → ... → ECL →
    TRACE_ANALYSIS → DEBUGGING → ECL → MONITOR. Modeled on CI/CD + OpenTelemetry.
    Every execution now produces health metrics, feedback signals, and FIR data.

Stage order (18 stages):
    1  SEE                  — evidence gathering + hash verification
    2  NORMALIZE_EVIDENCE   — ETL transform: raw receipts → structured atoms
    3  MMD                  — missing middle detection + coverage blocking
    4  DRS                  — decision records
    5  CDR                  — 7-pillar coding standards + POLICY_ENGINE
    6  OFM                  — outcome framing
    7  ADS                  — architecture decisions
    8  UXR                  — user requirements
    9  NUF                  — non-functional requirements
    10 SSO                  — scope outline
    11 RRP                  — repair and recovery plan
    12 IMPLEMENTATION       — build artifact
    13 VERIFICATION         — multi-check verification + POLICY_ENGINE
    14 TRACE_ANALYSIS       — span aggregation + anomaly detection
    15 DEBUGGING            — conditional on VERIFICATION (handled by runner)
    16 ECL                  — end condition lock (checks 15 prior stages)
    17 MONITOR              — health score + feedback loop

Post-run: call FIREngine.evaluate_session(state) for R12 meta-reflection.
"""

from __future__ import annotations

from typing import Any

# Update ECL's required stages list to include new stages
import STAGES as _stages_module
from MONITOR import MONITOR
from NORMALIZE_EVIDENCE import NORMALIZE_EVIDENCE
from STAGE_RUNNER import StageRunner
from STAGES import (
    ADS,
    CDR,
    DEBUGGING,
    DRS,
    ECL,
    IMPLEMENTATION,
    MMD,
    NUF,
    OFM,
    RRP,
    SEE,
    SSO,
    UXR,
    VERIFICATION,
)
from TRACE_ANALYSIS import TRACE_ANALYSIS

_stages_module.REQUIRED_PIPELINE_STAGES = [
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
    "TRACE_ANALYSIS",
    "DEBUGGING",
]


def run_mpp(task: dict[str, Any]) -> Any:
    stages = [
        SEE(),
        NORMALIZE_EVIDENCE(),
        MMD(),
        DRS(),
        CDR(),
        OFM(),
        ADS(),
        UXR(),
        NUF(),
        SSO(),
        RRP(),
        IMPLEMENTATION(),
        VERIFICATION(),
        TRACE_ANALYSIS(),
        DEBUGGING(),
        ECL(),
        MONITOR(),
    ]
    runner = StageRunner(stages)
    return runner.run(task)
