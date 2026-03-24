"""
SIE_ENGINE.py — Search Intent Engine with Exa neural retrieval
===============================================================

CDR V1 (Rationale):
    SIE generates sie_receipts for the SEE stage by running real web searches.
    Previously, sie_receipts were hand-authored in the task dict — meaning the
    LLM was writing its own evidence. SIE_ENGINE closes that gap: it takes an
    objective, generates dimension-specific queries, runs them through Exa, and
    returns receipts that SEE can validate with source="web.run".

    Three Exa capabilities improve on generic search:
      1. Neural semantic search — finds conceptually relevant results even when
         exact terms don't appear (better theory dimension coverage)
      2. search_and_contents with highlights — returns extracted key sentences,
         not just URLs. Each receipt has real content, not just a link.
      3. exa.research.create with output_schema — structured JSON extraction for
         the failure_modes dimension, where we need typed failure scenarios.

CDR V2 (Trust):
    Every receipt includes result_hash (SHA-256 of result text) for SEE
    verification. source is always "web.run" — the value SEE enforces.
    No receipt is fabricated. If Exa returns nothing, the dimension is empty
    and SEE will block (SEE_NO_EVIDENCE or SEE_COVERAGE_INCOMPLETE).

CDR V3 (Boundary):
    Inputs:  objective (str), dimensions (list), api_key (str)
    Outputs: list of sie_receipt dicts passable directly to task["sie_receipts"]
    Side effects: Exa API calls (billable per search)
    Assumptions: EXA_API_KEY env var set or api_key passed explicitly

CDR V4 (Failure):
    Exa API error: raises SIESearchError with dimension and query
    No results for dimension: returns receipt with result="" (SEE will block)
    Import failure (no exa-py): raises SIEConfigError at init time
    safe_state: partial results never silently pass — missing dimensions
    propagate as empty receipts that SEE_COVERAGE_INCOMPLETE will catch

CDR V5 (S-tier):
    result_hash on every receipt for SEE hash verification.
    Neural type for theory/implementation, keyword fallback for failure_modes.
    highlights extracted as result text — actual content, not just URL.
    research.create used for structured failure mode extraction when available.
"""

from __future__ import annotations

import hashlib
import os
from typing import Any

try:
    from exa_py import Exa

    _EXA_AVAILABLE = True
except ImportError:
    _EXA_AVAILABLE = False

# ── Constants ─────────────────────────────────────────────────────────────────

REQUIRED_DIMENSIONS = {"theory", "implementation", "failure_modes"}

# Query templates per dimension — Exa neural search works best with
# natural-language queries framed as statements, not keyword strings
DIMENSION_QUERY_TEMPLATES: dict[str, str] = {
    "theory": "theory principles and design patterns for {objective}",
    "implementation": "implementation guide how to build {objective}",
    "failure_modes": "failure modes problems errors pitfalls {objective}",
}

# Search type per dimension
# theory/implementation: neural (semantic match — finds conceptually related)
# failure_modes: keyword (find explicit error/failure mentions)
DIMENSION_SEARCH_TYPE: dict[str, str] = {
    "theory": "neural",
    "implementation": "neural",
    "failure_modes": "keyword",
}


# ── Exceptions ────────────────────────────────────────────────────────────────


class SIEConfigError(Exception):
    """exa-py not installed or API key missing."""


class SIESearchError(Exception):
    """Exa search call failed."""

    def __init__(self, dimension: str, query: str, cause: Exception) -> None:
        self.dimension = dimension
        self.query = query
        super().__init__(f"SIE_SEARCH_FAIL [{dimension}]: query='{query[:60]}' — {cause}")


# ── Engine ────────────────────────────────────────────────────────────────────


class SIEEngine:
    """
    Generates sie_receipts by running Exa searches per evidence dimension.

    Usage:
        engine = SIEEngine(api_key=os.environ["EXA_API_KEY"])
        receipts = engine.run("pipeline stage validation with hash verification")
        task["sie_receipts"] = receipts
        state = run_mpp(task)
    """

    def __init__(
        self,
        api_key: str | None = None,
        num_results: int = 3,
        max_highlight_chars: int = 800,
    ) -> None:
        if not _EXA_AVAILABLE:
            raise SIEConfigError("exa-py not installed. Run: pip install exa-py")

        resolved_key = api_key or os.environ.get("EXA_API_KEY", "")
        if not resolved_key:
            raise SIEConfigError("EXA_API_KEY not set. Export it or pass api_key= to SIEEngine().")

        self._exa = Exa(api_key=resolved_key)
        self._num_results = num_results
        self._max_highlight_chars = max_highlight_chars

    def run(
        self,
        objective: str,
        dimensions: list[str] | None = None,
        extra_queries: dict[str, str] | None = None,
    ) -> list[dict[str, Any]]:
        """
        Run SIE for an objective. Returns list of sie_receipt dicts.

        Args:
            objective: what is being researched (goes into query templates)
            dimensions: which dimensions to cover (default: all three required)
            extra_queries: override the query for a specific dimension
                          e.g. {"failure_modes": "common bugs in hash pipelines"}
        """
        dims = dimensions or list(REQUIRED_DIMENSIONS)
        extra = extra_queries or {}
        receipts: list[dict[str, Any]] = []

        for dim in dims:
            query = extra.get(dim) or DIMENSION_QUERY_TEMPLATES.get(dim, "{objective}").format(objective=objective)

            receipt = self._search_dimension(dim, query)
            receipts.append(receipt)

        return receipts

    def _search_dimension(self, dimension: str, query: str) -> dict[str, Any]:
        """Run one Exa search for one dimension. Returns a sie_receipt dict."""
        search_type = DIMENSION_SEARCH_TYPE.get(dimension, "neural")

        try:
            response = self._exa.search_and_contents(
                query,
                type=search_type,
                num_results=self._num_results,
                highlights={
                    "max_characters": self._max_highlight_chars,
                },
            )
        except Exception as e:
            raise SIESearchError(dimension, query, e) from e

        # Extract best highlight text from top results
        result_text = self._extract_result_text(response)

        return _build_receipt(
            dimension=dimension,
            result=result_text,
            query=query,
        )

    def _extract_result_text(self, response: Any) -> str:
        """
        Extract the most relevant text from Exa search response.
        Prefers highlights (pre-extracted key sentences) over full text.
        Combines highlights from top 3 results for richer evidence.
        """
        if not response.results:
            return ""

        parts: list[str] = []
        for result in response.results[:3]:
            highlights = getattr(result, "highlights", None) or []
            if highlights:
                # highlights is a list of pre-extracted relevant sentences
                parts.append(" ".join(h for h in highlights if h))
            else:
                # fallback: use beginning of text if available
                text = getattr(result, "text", "") or ""
                if text:
                    parts.append(text[:400])

        return " | ".join(p for p in parts if p)

    def run_structured(self, objective: str, dimension: str) -> dict[str, Any]:
        """
        Use exa.research.create for structured evidence extraction.
        Returns a receipt with JSON-structured result for failure_modes dimension.
        Best used when you need typed failure scenarios, not prose.
        """
        try:
            research = self._exa.research.create(
                instructions=(
                    f"Find the top failure modes, common errors, and known pitfalls "
                    f"when implementing: {objective}. "
                    f"For each failure mode state: what fails, why it fails, "
                    f"and how it is typically detected."
                ),
                output_schema={
                    "type": "object",
                    "properties": {
                        "failure_modes": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "name": {"type": "string"},
                                    "cause": {"type": "string"},
                                    "detectable_by": {"type": "string"},
                                },
                                "required": ["name", "cause", "detectable_by"],
                            },
                        }
                    },
                    "required": ["failure_modes"],
                },
            )
            # Extract structured content
            # research is a union type — guard against members without .output
            output = getattr(research, 'output', None)
            content = output.content if output else ""
            result_text = str(content) if content else ""
        except Exception:
            # Structured research not available — fall back to standard search
            return self._search_dimension(dimension, f"failure modes {objective}")

        return _build_receipt(dimension=dimension, result=result_text, query=objective)


# ── Receipt builder ───────────────────────────────────────────────────────────


def _build_receipt(
    dimension: str,
    result: str,
    query: str,
) -> dict[str, Any]:
    """
    Build a sie_receipt dict compatible with SEE stage validation.
    source is always 'web.run' — the value SEE enforces.
    result_hash is SHA-256 of result text for integrity verification.
    """
    result_hash = hashlib.sha256(result.encode()).hexdigest()
    return {
        "dimension": dimension,
        "result": result,
        "result_hash": result_hash,
        "source": "web.run",
        "query": query,
    }


# ── Convenience function ──────────────────────────────────────────────────────


def run_sie(
    objective: str,
    api_key: str | None = None,
    use_structured_failures: bool = False,
) -> list[dict[str, Any]]:
    """
    One-call interface. Run SIE for an objective, return sie_receipts.

    Args:
        objective: what is being researched
        api_key: Exa API key (falls back to EXA_API_KEY env var)
        use_structured_failures: use exa.research.create for failure_modes
                                  dimension (slower but more structured)

    Returns:
        list of 3 sie_receipt dicts (theory, implementation, failure_modes)

    Example:
        receipts = run_sie("SHA-256 hash verification in Python pipelines")
        task["sie_receipts"] = receipts
        state = run_mpp(task)
    """
    engine = SIEEngine(api_key=api_key)

    if use_structured_failures:
        receipts = engine.run(objective, dimensions=["theory", "implementation"])
        receipts.append(engine.run_structured(objective, "failure_modes"))
    else:
        receipts = engine.run(objective)

    return receipts
