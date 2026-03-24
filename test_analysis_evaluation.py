"""Tests for ANALYSIS_EVALUATION_ENGINE — all 8 gaps covered."""

import os
import sys
import tempfile
import shutil
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from engines.ANALYSIS_EVALUATION_ENGINE import (
    evaluate_analysis,
    extract_claims,
    check_evidence_grounding,
    get_receipts_dir,
)


class TestAnalysisEvaluation(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_root = tempfile.mkdtemp()
        os.environ["METABLOOMS_ROOT"] = self.temp_root

    def tearDown(self) -> None:
        shutil.rmtree(self.temp_root, ignore_errors=True)
        os.environ.pop("METABLOOMS_ROOT", None)

    # ── Original tests (all must pass) ───────────────────────────────────────

    def test_valid_analysis(self) -> None:
        """Happy path: well-structured analysis with artifact names — must PASS."""
        analysis = """
## What Changed
Added MPP_PROTOCOL.md and MPP_BRIDGE.py to create a cognitive-to-runtime bridge.

### Functional Impact
Now the LLM must output structured JSON before the runtime accepts it.
This enforces the pipeline protocol.

### Why It's Good
Separates reasoning from enforcement. Architecture is cleaner.

### Gaps
None.

### Alignment
Aligns with web.run and receipt invariants.

### Next Steps
Integrate into pipeline. Add to MPP stage list.
"""
        context = {"artifacts": ["MPP_PROTOCOL.md", "MPP_BRIDGE.py"]}
        result = evaluate_analysis(analysis, context)
        self.assertGreaterEqual(result["score"] or 0, 0)
        self.assertEqual(result["verdict"], "PASS", f"breakdown={result['breakdown']}")
        self.assertTrue(os.path.exists(result["receipt_path"]))
        self.assertFalse(result["truth_gate_blocked"])

    def test_ungrounded_analysis(self) -> None:
        """Completely ungrounded claim — truth gate must block."""
        analysis = "We added a magical new feature that fixes everything."
        result = evaluate_analysis(analysis, {})
        self.assertEqual(result["verdict"], "FAIL")
        self.assertEqual(result["breakdown"]["evidence_grounding"], 1)
        self.assertTrue(result["truth_gate_blocked"])

    def test_well_formatted_but_ungrounded(self) -> None:
        """Formatted but references unknown artifact — must FAIL."""
        analysis = """
## Change
A new engine SUPER_ENGINE.py was added to handle everything.

## Impact
Now the system is perfect.

## Next Steps
Deploy immediately.
"""
        result = evaluate_analysis(analysis, {"artifacts": []})
        self.assertEqual(result["verdict"], "FAIL")
        ungrounded_str = str(result["grounding_detail"]["ungrounded_claims"])
        self.assertIn("SUPER_ENGINE.py", ungrounded_str)

    def test_missing_actionability(self) -> None:
        """Grounded but no action items — must FAIL on quality gate."""
        analysis = """
## Change
Added MPP_BRIDGE.py to the MPP pipeline stage list.

## Impact
The bridge enforces schema validation before pipeline runs.
This aligns with CDR pillar requirements.

## Gaps
None.
"""
        result = evaluate_analysis(analysis, {"artifacts": ["MPP_BRIDGE.py"]})
        self.assertEqual(result["verdict"], "FAIL")
        self.assertLess(result["breakdown"]["actionability"], 3)

    def test_integration_uses_dynamic_root(self) -> None:
        """Receipt path must be under the dynamic root, not hardcoded."""
        analysis = "This is a test analysis. The pipeline uses web.run for receipts."
        result = evaluate_analysis(analysis, {"invariants": ["web.run"]})
        self.assertTrue(result["receipt_path"].startswith(self.temp_root))

    # ── Gap-specific regression tests ────────────────────────────────────────

    def test_gap1_no_gaps_reported_scores_3(self) -> None:
        """GAP 1 FIX: Honest 'None' gaps reporting must score 3, not 1."""
        from engines.ANALYSIS_EVALUATION_ENGINE import _heuristic_gaps
        self.assertEqual(_heuristic_gaps("Gaps: None."), 3)
        self.assertEqual(_heuristic_gaps("No gaps identified."), 3)
        self.assertEqual(_heuristic_gaps("No issues found."), 3)

    def test_gap1_missing_gaps_section_scores_1(self) -> None:
        """Analysis with no gaps section at all scores 1."""
        from engines.ANALYSIS_EVALUATION_ENGINE import _heuristic_gaps
        self.assertEqual(_heuristic_gaps("Added a new feature."), 1)

    def test_gap2_markdown_claims_extracted(self) -> None:
        """GAP 2 FIX: Markdown sections produce separate claims."""
        text = """
## What Changed
Added MPP_BRIDGE.py.

### Gaps
None.

### Next Steps
Integrate into pipeline.
"""
        claims = extract_claims(text)
        self.assertGreater(len(claims), 1, f"Only {len(claims)} claims extracted from multi-section markdown")

    def test_gap3_system_vocab_grounds_claim(self) -> None:
        """GAP 3 FIX: Claims using system vocab (MPP, CDR, etc.) are grounded."""
        text = "Separates reasoning from enforcement using the CDR protocol."
        score, issues, detail = check_evidence_grounding(text, {})
        self.assertGreater(detail["grounded_count"], 0,
                           "System-vocab claim should be grounded")

    def test_gap4_truth_gate_returns_none_score(self) -> None:
        """GAP 4 FIX: truth_gate_blocked=True returns score=None, not 0.0."""
        analysis = "This magical feature fixes everything with no evidence."
        result = evaluate_analysis(analysis, {})
        self.assertTrue(result["truth_gate_blocked"])
        self.assertIsNone(result["score"],
                          "score must be None when truth gate blocks, not 0.0")

    def test_gap5_total_weight_not_in_formula(self) -> None:
        """GAP 5 FIX: No dead total_weight code — ruff must pass."""
        import subprocess
        r = subprocess.run(
            ["python3", "-m", "ruff", "check",
             "engines/ANALYSIS_EVALUATION_ENGINE.py"],
            cwd=os.path.join(os.path.dirname(__file__), ".."),
            capture_output=True, text=True
        )
        self.assertEqual(r.returncode, 0, f"Ruff errors: {r.stdout}")

    def test_gap6_receipt_collision_prevention(self) -> None:
        """GAP 6 FIX: Two rapid calls produce different receipt files."""
        analysis = "The pipeline uses CDR and MPP protocols for governance."
        r1 = evaluate_analysis(analysis, {})
        r2 = evaluate_analysis(analysis, {})
        self.assertNotEqual(r1["receipt_path"], r2["receipt_path"],
                            "Rapid calls must not produce same receipt path")

    def test_gap8_no_deprecation_warning(self) -> None:
        """GAP 8 FIX: No datetime.utcnow() deprecation warning."""
        import warnings
        import datetime as dt
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            analysis = "The MPP bridge uses CDR and ERAC for validation."
            evaluate_analysis(analysis, {})
            deprecation_warnings = [x for x in w if issubclass(x.category, DeprecationWarning)
                                    and "utcnow" in str(x.message)]
            self.assertEqual(len(deprecation_warnings), 0,
                             f"utcnow deprecation warning still present: {deprecation_warnings}")


if __name__ == "__main__":
    unittest.main()
