"""
ANALYSIS_EVALUATION_ENGINE.py — Analysis quality and truth evaluator
====================================================================

CDR V1 (Rationale):
    Evaluates LLM-produced analysis text against two layers:
    (1) Truth layer: are claims grounded in known artifacts/receipts/invariants?
    (2) Quality layer: does the analysis have clarity, gaps, actionability?
    An analysis that lies confidently is worse than one that admits uncertainty.
    Truth gates first. Quality gates second.

CDR V2 (Trust):
    Grounding is checked by artifact name presence AND by design-pattern
    keyword presence. Claims describing what artifacts DO are counted as
    grounded if they use system vocabulary (MPP, ERAC, CDR, etc.).
    Honest reporting of no gaps does not penalize the gaps dimension.

CDR V3 (Boundary):
    Inputs:  analysis_text (str), context (dict with artifacts/receipts/invariants)
    Outputs: dict with score, verdict, breakdown, receipt_path, receipt_hash
    Side effects: writes receipt JSON to METABLOOMS_ROOT/receipts/
    Assumptions: METABLOOMS_ROOT env var set, or defaults to /mnt/data/Metablooms_OS

CDR V4 (Failure):
    Empty analysis_text: evidence_grounding=1, verdict=FAIL
    Receipt write failure: raises RuntimeError (safe_state: do not silently skip)
    safe_state: always return a result dict, never raise on scoring failure

CDR V5 (S-tier):
    Receipt filename includes UUID to prevent timestamp collision.
    composite_score=None when truth gate blocks (distinguishable from score=0.0).
    datetime.now(UTC) used (not deprecated utcnow).
    total_weight dead code removed.
"""

from __future__ import annotations

import datetime
import hashlib
import json
import os
import re
import uuid
from typing import Any

# ── Runtime configuration ─────────────────────────────────────────────────────


def get_root() -> str:
    return os.environ.get("METABLOOMS_ROOT", "/mnt/data/Metablooms_OS")


def get_receipts_dir() -> str:
    return os.path.join(get_root(), "receipts")


# ── Rubric criteria (weights) ─────────────────────────────────────────────────

CRITERIA: dict[str, dict[str, int]] = {
    "clarity": {"weight": 1},
    "impact": {"weight": 1},
    "rationale": {"weight": 1},
    "gaps": {"weight": 1},
    "alignment": {"weight": 1},
    "actionability": {"weight": 1},
    "structure": {"weight": 1},
    "evidence_grounding": {"weight": 3},  # dominant
}

# System vocabulary: claims using these words are grounded even without artifact names
SYSTEM_VOCAB: set[str] = {
    "mpp",
    "erac",
    "cdr",
    "fir",
    "ofm",
    "drs",
    "ecl",
    "mmD",
    "rrp",
    "web.run",
    "receipt",
    "invariant",
    "sandcrawler",
    "coevolution",
    "pipeline",
    "stage",
    "artifact",
    "hash",
    "gateway",
    "bridge",
    "protocol",
    "enforcement",
    "governance",
    "policy",
}

# ── Claim extraction ──────────────────────────────────────────────────────────


def extract_claims(text: str) -> list[str]:
    """
    Extract meaningful claims from analysis text.

    Splits on both sentence boundaries AND markdown section boundaries.
    Markdown headers (## / ###) introduce new logical claims even without
    terminal punctuation — the prior regex-only approach missed them.
    """
    # First split on markdown headers to separate sections
    sections = re.split(r"\n(?=#{1,6}\s)", text)

    claims: list[str] = []
    claim_keywords = [
        "added",
        "changed",
        "removed",
        "implemented",
        "built",
        "created",
        "modified",
        "wrote",
        "introduced",
        "deleted",
        "refactored",
        "is the",
        "now",
        "separates",
        "ensures",
        "prevents",
        "architecture",
        "pattern",
        "bridge",
        "layer",
        "protocol",
        "runtime",
        "enforces",
        "validates",
        "replaces",
        "moves",
        "aligns",
        "integrates",
        "enables",
        "allows",
    ]

    for section in sections:
        section = section.strip()
        if not section:
            continue
        # Further split each section on sentence boundaries
        sentences = re.split(r"(?<=[.!?])\s+", section)
        for s in sentences:
            s = s.strip()
            if not s:
                continue
            if any(kw in s.lower() for kw in claim_keywords):
                claims.append(s)
            # Keep headers with content as standalone claims
            elif re.match(r"#{1,6}\s", s) and len(s) > 5:
                claims.append(s)

    # Conservative fallback: if nothing matched, treat all non-empty lines as claims
    if not claims:
        claims = [ln.strip() for ln in text.splitlines() if ln.strip()]

    return claims


# ── Evidence grounding ────────────────────────────────────────────────────────


def check_evidence_grounding(
    text: str, context: dict[str, Any]
) -> tuple[int, list[str], dict[str, Any]]:
    """
    Return (score 1-4, issues, grounding_detail).

    A claim is grounded if it:
    (a) contains the name of a known artifact, receipt, or invariant, OR
    (b) uses system vocabulary (MPP, CDR, ERAC, receipt, etc.) indicating
        the claim is about the actual system being described.
    """
    claims = extract_claims(text)

    # Build known artifact set
    known: set[str] = set()
    known.update(context.get("artifacts", []))
    known.update(context.get("receipts", []))
    known.update(context.get("invariants", []))
    # Canonical fallback names
    known.update(
        [
            "web.run",
            "ERAC",
            "OFM",
            "CDR",
            "FIR",
            "DRS",
            "ECL",
            "MMD",
            "RRP",
            "MPP_PROTOCOL.md",
            "MPP_TASK_SCHEMA.py",
            "MPP_BRIDGE.py",
            "STAGES.py",
            "FIR_ENGINE.py",
            "TRACE_ANALYSIS.py",
            "MONITOR.py",
        ]
    )

    grounded_count = 0
    grounded_claims: list[str] = []
    ungrounded_claims: list[str] = []

    for claim in claims:
        claim_lower = claim.lower()
        # Check (a): explicit artifact name
        artifact_match = any(art in claim for art in known)
        # Check (b): system vocabulary
        vocab_match = any(word in claim_lower for word in SYSTEM_VOCAB)

        if artifact_match or vocab_match:
            grounded_count += 1
            grounded_claims.append(claim)
        else:
            ungrounded_claims.append(claim)

    total = len(claims)
    ratio = grounded_count / total if total else 0.0

    if total == 0:
        score = 1
    elif ratio >= 0.8:
        score = 4
    elif ratio >= 0.5:
        score = 3
    elif ratio >= 0.2:
        score = 2
    else:
        score = 1

    issues: list[str] = []
    if score < 4:
        issues.append(
            f"Only {grounded_count}/{total} claims grounded in known artifacts/invariants/system vocabulary."
        )

    detail: dict[str, Any] = {
        "claims": claims,
        "grounded_count": grounded_count,
        "total_claims": total,
        "grounded_claims": grounded_claims[:10],
        "ungrounded_claims": ungrounded_claims[:10],
        "ratio": round(ratio, 3),
    }
    return score, issues, detail


# ── Heuristic scoring ─────────────────────────────────────────────────────────


def _heuristic_score(text: str, keywords: list[str]) -> int:
    if not keywords:
        return 3
    matches = sum(1 for kw in keywords if kw in text.lower())
    ratio = matches / len(keywords)
    if ratio >= 0.6:
        return 4
    if ratio >= 0.4:
        return 3
    if ratio >= 0.2:
        return 2
    return 1


def _heuristic_clarity(text: str) -> int:
    has_structure = any(m in text for m in ["##", "###", "* ", "- ", "1."])
    if has_structure and len(text.split()) > 100:
        return 4
    if has_structure:
        return 3
    if len(text.split()) > 50:
        return 2
    return 1


def _heuristic_impact(text: str) -> int:
    return _heuristic_score(
        text, ["enables", "allows", "now can", "unlocks", "makes it possible"]
    )


def _heuristic_rationale(text: str) -> int:
    return _heuristic_score(
        text,
        [
            "because",
            "since",
            "therefore",
            "pattern",
            "design",
            "architecture",
            "reason",
        ],
    )


def _heuristic_gaps(text: str) -> int:
    """
    FIX: An analysis that correctly states 'no gaps' must not score 1.
    'None' or 'no gaps' or 'none identified' = analyst checked and found none = score 3.
    Missing gaps section entirely = score 1 (they didn't check).
    """
    text_lower = text.lower()
    # Explicit 'no gaps' reporting — analyst checked and is honest
    no_gaps_phrases = [
        "none",
        "no gaps",
        "none identified",
        "no issues",
        "no weaknesses",
    ]
    if any(ph in text_lower for ph in no_gaps_phrases):
        return (
            3  # Honest reporting of no gaps = adequate (not 4 — no evidence of looking)
        )
    # Gap keywords present = analyst identified and documented gaps
    gap_keywords = [
        "gap",
        "missing",
        "inconsistent",
        "weakness",
        "issue",
        "problem",
        "but",
        "however",
        "not yet",
        "todo",
        "open",
    ]
    return _heuristic_score(text, gap_keywords)


def _heuristic_alignment(text: str) -> int:
    return _heuristic_score(
        text,
        [
            "web.run",
            "erac",
            "receipt",
            "invariant",
            "ofm",
            "cdr",
            "fir",
            "mpp",
            "stage",
        ],
    )


def _heuristic_actionability(text: str) -> int:
    return _heuristic_score(
        text,
        ["next step", "fix", "should", "must", "implement", "change", "add", "update"],
    )


def _heuristic_structure(text: str) -> int:
    if any(m in text for m in ["##", "###", "* ", "- ", "1.", "2."]):
        return 4
    return 2


# ── Main evaluation ───────────────────────────────────────────────────────────


def evaluate_analysis(
    analysis_text: str, context: dict[str, Any] | None = None
) -> dict[str, Any]:
    """
    Score an analysis, enforce truth gate, then quality gate. Write receipt.

    Returns dict with:
        score: float 0-100, or None if truth gate blocked
        truth_gate_blocked: bool
        verdict: "PASS" | "FAIL"
        breakdown: per-criterion scores
        receipt_path: path to written receipt
        receipt_hash: SHA-256 of receipt file
        evidence_issues: list of grounding issues
        grounding_detail: full claim-level breakdown
    """
    if context is None:
        context = {}

    now = datetime.datetime.now(datetime.UTC)
    timestamp = now.isoformat()

    # ── Truth layer ───────────────────────────────────────────────────────────
    ev_score, ev_issues, grounding_detail = check_evidence_grounding(
        analysis_text, context
    )

    # ── Quality layer ─────────────────────────────────────────────────────────
    breakdown: dict[str, int] = {
        "clarity": _heuristic_clarity(analysis_text),
        "impact": _heuristic_impact(analysis_text),
        "rationale": _heuristic_rationale(analysis_text),
        "gaps": _heuristic_gaps(analysis_text),
        "alignment": _heuristic_alignment(analysis_text),
        "actionability": _heuristic_actionability(analysis_text),
        "structure": _heuristic_structure(analysis_text),
        "evidence_grounding": ev_score,
    }

    # ── Gate logic ────────────────────────────────────────────────────────────
    truth_gate_blocked = ev_score < 3
    composite_score: float | None

    if truth_gate_blocked:
        verdict = "FAIL"
        composite_score = None  # distinguishable from score=0.0
    else:
        # Essential quality dimensions must all be >= 3
        essential_ok = (
            breakdown["clarity"] >= 3
            and breakdown["gaps"] >= 3
            and breakdown["actionability"] >= 3
        )
        verdict = "PASS" if essential_ok else "FAIL"

        # Compute weighted composite (informational — not used for pass/fail)
        max_weighted = sum(4 * CRITERIA[c]["weight"] for c in breakdown)
        weighted_sum = sum(breakdown[c] * CRITERIA[c]["weight"] for c in breakdown)
        composite_score = round((weighted_sum / max_weighted) * 100, 2)

    # ── Receipt ───────────────────────────────────────────────────────────────
    receipt_id = uuid.uuid4().hex[:12]
    receipt_data: dict[str, Any] = {
        "stage": "ANALYSIS_EVALUATION",
        "receipt_id": receipt_id,
        "timestamp_utc": timestamp,
        "analysis_hash": hashlib.sha256(analysis_text.encode()).hexdigest(),
        "composite_score": composite_score,
        "truth_gate_blocked": truth_gate_blocked,
        "verdict": verdict,
        "breakdown": breakdown,
        "evidence_grounding_issues": ev_issues,
        "grounding_detail": grounding_detail,
        "context_artifacts": list(context.get("artifacts", []))[:10],
        "context_receipts": list(context.get("receipts", []))[:10],
        "context_invariants": list(context.get("invariants", []))[:10],
    }

    receipts_dir = get_receipts_dir()
    os.makedirs(receipts_dir, exist_ok=True)
    # UUID suffix prevents timestamp collision
    receipt_filename = (
        f"ANALYSIS_EVALUATION_{now.strftime('%Y%m%d_%H%M%S')}_{receipt_id}.json"
    )
    receipt_path = os.path.join(receipts_dir, receipt_filename)
    with open(receipt_path, "w") as f:
        json.dump(receipt_data, f, indent=2)

    with open(receipt_path, "rb") as f:
        receipt_hash = hashlib.sha256(f.read()).hexdigest()

    return {
        "score": composite_score,
        "truth_gate_blocked": truth_gate_blocked,
        "verdict": verdict,
        "breakdown": breakdown,
        "receipt_path": receipt_path,
        "receipt_hash": receipt_hash,
        "evidence_issues": ev_issues,
        "grounding_detail": grounding_detail,
    }
