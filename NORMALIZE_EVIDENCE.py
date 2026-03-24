"""
NORMALIZE_EVIDENCE.py — Evidence normalization layer (ETL model, Transform step)
=================================================================================

CDR V1 (Rationale):
    Raw SEE receipts contain unstructured result strings from web.run. Downstream
    stages (MMD, CDR, VERIFICATION) currently operate on raw strings. This creates
    inconsistency — the same evidence looks different depending on how web.run
    formatted its response. Normalization produces a structured, canonical evidence
    atom from each receipt before any stage consumes it.

CDR V2 (Trust):
    Normalization is deterministic. Same raw input always produces same atom.
    No inference, no enrichment — only structure extraction and classification.

CDR V3 (Boundary):
    Receives sie_receipts from task. Produces normalized_evidence list.
    Does not modify receipts. Does not re-validate hashes (SEE already did that).

CDR V4 (Failure):
    Missing result field → atom flagged as MALFORMED, pipeline blocks.
    Empty result → atom flagged as EMPTY, pipeline blocks.
    Unknown dimension → atom flagged as UNCLASSIFIED, warning only.

Integration contract:
    Inputs:  state.task['sie_receipts'] (validated by SEE)
    Outputs: state.task['normalized_evidence'] (list of EvidenceAtom dicts)
    Side effects: none
    Assumptions: SEE has already run and validated all receipts
"""

from __future__ import annotations

from typing import Any

from STAGE_BASE import StageBase

KNOWN_DIMENSIONS: set[str] = {"theory", "implementation", "failure_modes"}

# Minimum meaningful evidence length (chars)
MIN_EVIDENCE_LENGTH: int = 10


class EvidenceAtom:
    """Canonical structure for a single normalized evidence item."""

    def __init__(
        self,
        atom_id: str,
        dimension: str,
        raw_result: str,
        query: str,
        result_hash: str,
        quality: str,  # GOOD | THIN | EMPTY | MALFORMED
        word_count: int,
        classified: bool,
    ) -> None:
        self.atom_id = atom_id
        self.dimension = dimension
        self.raw_result = raw_result
        self.query = query
        self.result_hash = result_hash
        self.quality = quality
        self.word_count = word_count
        self.classified = classified

    def to_dict(self) -> dict[str, Any]:
        return {
            "atom_id": self.atom_id,
            "dimension": self.dimension,
            "raw_result": self.raw_result,
            "query": self.query,
            "result_hash": self.result_hash,
            "quality": self.quality,
            "word_count": self.word_count,
            "classified": self.classified,
        }


def _classify_quality(result: str) -> tuple[str, int]:
    """Classify evidence quality from raw result string."""
    if not result or not result.strip():
        return "EMPTY", 0
    word_count = len(result.split())
    if len(result) < MIN_EVIDENCE_LENGTH:
        return "THIN", word_count
    return "GOOD", word_count


class NORMALIZE_EVIDENCE(StageBase):
    name = "NORMALIZE_EVIDENCE"

    def execute(self, state: Any) -> dict[str, Any]:
        receipts: list[dict[str, Any]] = state.task.get("sie_receipts", [])

        if not receipts:
            raise RuntimeError("NORMALIZE_EVIDENCE_NO_RECEIPTS: sie_receipts missing — SEE must run first")

        atoms: list[dict[str, Any]] = []
        blocking_issues: list[str] = []

        for i, r in enumerate(receipts):
            raw = r.get("result", "")
            dim = r.get("dimension", "UNKNOWN")
            query = r.get("query", "")
            result_hash = r.get("result_hash", "")

            if raw is None:
                blocking_issues.append(f"ATOM[{i}] result is None — MALFORMED")
                continue

            quality, word_count = _classify_quality(str(raw))

            if quality == "EMPTY":
                blocking_issues.append(f"ATOM[{i}] dimension={dim} result is empty")
                continue

            classified = dim in KNOWN_DIMENSIONS

            atom = EvidenceAtom(
                atom_id=f"ATOM-{i:03d}-{dim[:4].upper()}",
                dimension=dim,
                raw_result=str(raw),
                query=query,
                result_hash=result_hash,
                quality=quality,
                word_count=word_count,
                classified=classified,
            )
            atoms.append(atom.to_dict())

        if blocking_issues:
            raise RuntimeError(f"NORMALIZE_EVIDENCE_MALFORMED: {blocking_issues}")

        # Inject normalized evidence into task for downstream stages
        state.task["normalized_evidence"] = atoms

        thin_count = sum(1 for a in atoms if a["quality"] == "THIN")
        good_count = sum(1 for a in atoms if a["quality"] == "GOOD")

        return {
            "atom_count": len(atoms),
            "good_count": good_count,
            "thin_count": thin_count,
            "dimensions_normalized": sorted({a["dimension"] for a in atoms}),
            "normalization_complete": True,
        }
