from __future__ import annotations

import hashlib
from typing import Any

from STAGE_BASE import StageBase

# ── Constants ──────────────────────────────────────────────────────────────────

REQUIRED_COVERAGE_DIMS: set[str] = {"theory", "implementation", "failure_modes"}

REQUIRED_PIPELINE_STAGES: list[str] = [
    "SEE",
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
    "DEBUGGING",
]

CDR_SEVEN_PILLARS: list[str] = [
    "proactive_rationale",
    "explicit_constraint_mapping",
    "semantic_domain_authority",
    "anticipated_failure_intent",
    "integration_reciprocity",
    "history_aware_evolution",
    "mandatory_attestation",
]

CDR_FORBIDDEN_NAMES: set[str] = {"utils", "helpers", "misc", "tools", "common", "stuff"}


# ══════════════════════════════════════════════════════════════════════════════
# STAGE 1 — SEE  (Sandcrawler Evidence Engine)
# ══════════════════════════════════════════════════════════════════════════════
class SEE(StageBase):
    name = "SEE"

    def execute(self, state: Any) -> dict[str, Any]:
        receipts = state.task.get("sie_receipts")
        if not receipts:
            raise RuntimeError("SEE_NO_EVIDENCE: sie_receipts missing or empty")

        validated: list[dict[str, Any]] = []
        for i, r in enumerate(receipts):
            # FIX: source must be web.run
            if r.get("source", "web.run") != "web.run":
                raise RuntimeError(f"SEE_NOT_REAL_WEB_RUN: receipt[{i}] source={r.get('source')}")
            # FIX: result must exist
            if "result" not in r:
                raise RuntimeError(f"SEE_RESULT_MISSING: receipt[{i}] has no result field")
            # FIX: hash must match content
            expected_hash = r.get("result_hash")
            if expected_hash:
                actual_hash = hashlib.sha256(str(r["result"]).encode()).hexdigest()
                if actual_hash != expected_hash:
                    raise RuntimeError(
                        f"SEE_HASH_MISMATCH: receipt[{i}] " f"expected={expected_hash[:12]} actual={actual_hash[:12]}"
                    )
            validated.append(r)

        return {
            "evidence_count": len(validated),
            "dimensions_covered": list({r.get("dimension") for r in validated if r.get("dimension")}),
        }


# ══════════════════════════════════════════════════════════════════════════════
# STAGE 2 — MMD  (Missing Middle Detector)
# ══════════════════════════════════════════════════════════════════════════════
class MMD(StageBase):
    name = "MMD"

    def execute(self, state: Any) -> dict[str, Any]:
        gaps: list[dict[str, Any]] = []

        if "SEE" not in state.data:
            gaps.append({"gap": "MISSING_SEE", "severity": "critical"})
            raise RuntimeError(f"MMD_CRITICAL_GAP: {gaps}")

        see_artifact = state.data["SEE"].get("artifact", {})
        evidence_count = see_artifact.get("evidence_count", 0)

        if evidence_count == 0:
            gaps.append(
                {
                    "gap": "SEE_ZERO_EVIDENCE",
                    "severity": "critical",
                    "detail": "SEE ran but collected no evidence",
                }
            )

        sie_plan = state.task.get("sie_plan")
        sie_receipts = state.task.get("sie_receipts", [])

        if sie_plan and not sie_receipts:
            gaps.append(
                {
                    "gap": "PLAN_NO_RECEIPTS",
                    "severity": "high",
                    "detail": "SIE plan exists but no execution receipts",
                }
            )

        if sie_receipts:
            covered = {r.get("dimension") for r in sie_receipts if r.get("dimension")}
            missing_dims = REQUIRED_COVERAGE_DIMS - covered
            if missing_dims:
                gaps.append(
                    {
                        "gap": "COVERAGE_INCOMPLETE",
                        "severity": "high",
                        "detail": f"Missing dimensions: {sorted(missing_dims)}",
                    }
                )

        # FIX: block on any critical gap
        if any(g["severity"] == "critical" for g in gaps):
            raise RuntimeError(f"MMD_CRITICAL_GAP: {[g['gap'] for g in gaps if g['severity'] == 'critical']}")

        return {
            "gaps": gaps,
            "gap_count": len(gaps),
            "evidence_count_seen": evidence_count,
        }


# ══════════════════════════════════════════════════════════════════════════════
# STAGE 3 — DRS  (Decision Record System)
# ══════════════════════════════════════════════════════════════════════════════
class DRS(StageBase):
    name = "DRS"

    def execute(self, state: Any) -> dict[str, Any]:
        task_input = state.task.get("input", "")
        objective_id = state.task.get("objective_id", "OBJ-UNKNOWN")

        # Pull existing decisions from task if caller pre-loaded them
        provided = state.task.get("drs_decisions", [])

        # Auto-generate a baseline decision record from what we know so far
        auto_decision: dict[str, Any] = {
            "decision_id": f"DRS-AUTO-{objective_id}",
            "decision": f"Proceed with implementation of: {task_input[:80]}",
            "rationale": "SEE evidence gathered, MMD gaps resolved, proceeding to CDR constraints",
            "alternatives_considered": [
                "Abort if evidence insufficient (rejected: SEE passed)",
                "Defer to next cycle (rejected: objective is active)",
            ],
            "decided_by": "MPP_AUTO",
            "stage_evidence": {
                "see_evidence_count": state.data.get("SEE", {}).get("artifact", {}).get("evidence_count", 0),
                "mmd_gap_count": state.data.get("MMD", {}).get("artifact", {}).get("gap_count", 0),
            },
        }

        decisions = provided if provided else [auto_decision]

        # Validate: every decision must have decision_id, decision, rationale, alternatives_considered
        for d in decisions:
            for field in ("decision_id", "decision", "rationale", "alternatives_considered"):
                if field not in d:
                    raise RuntimeError(f"DRS_INVALID_RECORD: missing field '{field}' in decision")
            if not d["alternatives_considered"]:
                raise RuntimeError(f"DRS_NO_ALTERNATIVES: decision {d['decision_id']} has no alternatives_considered")

        return {
            "decisions": decisions,
            "decision_count": len(decisions),
            "objective_id": objective_id,
        }


# ══════════════════════════════════════════════════════════════════════════════
# STAGE 4 — CDR  (Coding Done Right)  — IN-DEPTH per canonical spec
# ══════════════════════════════════════════════════════════════════════════════
class CDR(StageBase):
    name = "CDR"

    # Violation severity levels
    SEVERITY_CRITICAL = "critical"  # blocks pipeline
    SEVERITY_HIGH = "high"  # blocks pipeline
    SEVERITY_WARN = "warn"  # logged, does not block

    def _check_pillar_1_proactive_rationale(self, constraints: dict[str, Any]) -> list[dict[str, Any]]:
        violations = []
        rationale = constraints.get("rationale")
        if not rationale:
            violations.append(
                {
                    "pillar": 1,
                    "name": "proactive_rationale",
                    "severity": self.SEVERITY_CRITICAL,
                    "detail": "No rationale provided. CDR requires WHY before WHAT.",
                }
            )
        elif len(str(rationale)) < 20:
            violations.append(
                {
                    "pillar": 1,
                    "name": "proactive_rationale",
                    "severity": self.SEVERITY_HIGH,
                    "detail": f"Rationale too brief ({len(str(rationale))} chars). Must explain purpose, not label it.",
                }
            )
        return violations

    def _check_pillar_2_constraint_mapping(self, constraints: dict[str, Any]) -> list[dict[str, Any]]:
        violations = []
        explicit_constraints = constraints.get("constraints", [])
        if not explicit_constraints:
            violations.append(
                {
                    "pillar": 2,
                    "name": "explicit_constraint_mapping",
                    "severity": self.SEVERITY_HIGH,
                    "detail": "No constraints declared. Every solution must state what limits apply.",
                }
            )
        return violations

    def _check_pillar_3_semantic_domain_authority(self, constraints: dict[str, Any]) -> list[dict[str, Any]]:
        violations = []
        module_name = constraints.get("module_name", "")
        if module_name:
            base = module_name.lower().replace(".py", "").replace("_engine", "").replace("_final", "")
            if base in CDR_FORBIDDEN_NAMES:
                violations.append(
                    {
                        "pillar": 3,
                        "name": "semantic_domain_authority",
                        "severity": self.SEVERITY_CRITICAL,
                        "detail": (
                            f"Module name '{module_name}' is a junk-drawer name. "
                            f"Forbidden: {CDR_FORBIDDEN_NAMES}. "
                            "Use law-bearing names: AdmissionGate, EvidenceResolver, etc."
                        ),
                    }
                )
        return violations

    def _check_pillar_4_anticipated_failure_intent(self, constraints: dict[str, Any]) -> list[dict[str, Any]]:
        violations = []
        failure_modes = constraints.get("failure_modes", [])
        if not failure_modes:
            violations.append(
                {
                    "pillar": 4,
                    "name": "anticipated_failure_intent",
                    "severity": self.SEVERITY_HIGH,
                    "detail": "No failure modes declared. Every function that can fail must document how and the safe state.",
                }
            )
        else:
            for fm in failure_modes:
                if "safe_state" not in fm:
                    violations.append(
                        {
                            "pillar": 4,
                            "name": "anticipated_failure_intent",
                            "severity": self.SEVERITY_WARN,
                            "detail": f"Failure mode '{fm.get('mode', 'unknown')}' has no safe_state declared.",
                        }
                    )
        return violations

    def _check_pillar_5_integration_reciprocity(self, constraints: dict[str, Any]) -> list[dict[str, Any]]:
        violations = []
        contract = constraints.get("integration_contract", {})
        required_fields = ("inputs", "outputs", "side_effects", "assumptions")
        missing = [f for f in required_fields if f not in contract]
        if missing:
            violations.append(
                {
                    "pillar": 5,
                    "name": "integration_reciprocity",
                    "severity": self.SEVERITY_HIGH,
                    "detail": f"integration_contract missing: {missing}. Modules must declare their full contract.",
                }
            )
        return violations

    def _check_pillar_6_history_aware_evolution(self, constraints: dict[str, Any]) -> list[dict[str, Any]]:
        violations = []
        is_delta = constraints.get("is_delta", False)
        if is_delta:
            supersedes = constraints.get("supersedes")
            supersession_reason = constraints.get("supersession_reason")
            if not supersedes:
                violations.append(
                    {
                        "pillar": 6,
                        "name": "history_aware_evolution",
                        "severity": self.SEVERITY_HIGH,
                        "detail": "Delta declared but no 'supersedes' field. Every change must name what it replaces.",
                    }
                )
            if not supersession_reason:
                violations.append(
                    {
                        "pillar": 6,
                        "name": "history_aware_evolution",
                        "severity": self.SEVERITY_HIGH,
                        "detail": "Delta declared but no 'supersession_reason'. Explain why prior logic became invalid.",
                    }
                )
        return violations

    def _check_pillar_7_mandatory_attestation(self, constraints: dict[str, Any]) -> list[dict[str, Any]]:
        violations = []
        attestation = constraints.get("attestation")
        if not attestation:
            violations.append(
                {
                    "pillar": 7,
                    "name": "mandatory_attestation",
                    "severity": self.SEVERITY_CRITICAL,
                    "detail": (
                        "No attestation provided. The generator must be able to reconstruct "
                        "and attest to the reasoning chain. Unattested code is invalid."
                    ),
                }
            )
        return violations

    def execute(self, state: Any) -> dict[str, Any]:
        constraints: dict[str, Any] = state.task.get("cdr_constraints", {})

        all_violations: list[dict[str, Any]] = []
        all_violations += self._check_pillar_1_proactive_rationale(constraints)
        all_violations += self._check_pillar_2_constraint_mapping(constraints)
        all_violations += self._check_pillar_3_semantic_domain_authority(constraints)
        all_violations += self._check_pillar_4_anticipated_failure_intent(constraints)
        all_violations += self._check_pillar_5_integration_reciprocity(constraints)
        all_violations += self._check_pillar_6_history_aware_evolution(constraints)
        all_violations += self._check_pillar_7_mandatory_attestation(constraints)

        blocking = [v for v in all_violations if v["severity"] in (self.SEVERITY_CRITICAL, self.SEVERITY_HIGH)]
        warnings = [v for v in all_violations if v["severity"] == self.SEVERITY_WARN]

        if blocking:
            pillar_names = [v["name"] for v in blocking]
            raise RuntimeError(f"CDR_VIOLATION: blocking pillars failed: {pillar_names}")

        pillars_checked = [p for p in CDR_SEVEN_PILLARS]
        pillars_passed = [p for p in pillars_checked if not any(v["name"] == p for v in blocking)]

        return {
            "cdr_compliant": True,
            "pillars_checked": pillars_checked,
            "pillars_passed": pillars_passed,
            "violations": all_violations,
            "violation_count": len(all_violations),
            "blocking_count": len(blocking),
            "warning_count": len(warnings),
        }


# ══════════════════════════════════════════════════════════════════════════════
# STAGE 5 — OFM  (Outcome Framing Matrix)
# ══════════════════════════════════════════════════════════════════════════════
class OFM(StageBase):
    name = "OFM"

    def execute(self, state: Any) -> dict[str, Any]:
        ofm = state.task.get("ofm", {})

        objective_id = ofm.get("objective_id") or state.task.get("objective_id", "OBJ-UNKNOWN")
        success_criteria: list[str] = ofm.get("success_criteria", [])
        failure_criteria: list[str] = ofm.get("failure_criteria", [])

        if not success_criteria:
            raise RuntimeError("OFM_NO_SUCCESS_CRITERIA: cannot proceed without defining what done looks like")
        if not failure_criteria:
            raise RuntimeError("OFM_NO_FAILURE_CRITERIA: must define what failure looks like, not just success")

        # Pull DRS decisions to anchor the objective
        drs_decisions = state.data.get("DRS", {}).get("artifact", {}).get("decisions", [])
        decision_ids = [d.get("decision_id") for d in drs_decisions]

        return {
            "objective_id": objective_id,
            "success_criteria": success_criteria,
            "failure_criteria": failure_criteria,
            "criteria_count": len(success_criteria) + len(failure_criteria),
            "anchored_to_decisions": decision_ids,
        }


# ══════════════════════════════════════════════════════════════════════════════
# STAGE 6 — ADS  (Architecture Decision Set)
# ══════════════════════════════════════════════════════════════════════════════
class ADS(StageBase):
    name = "ADS"

    def execute(self, state: Any) -> dict[str, Any]:
        ads = state.task.get("ads", {})

        engine_list: list[str] = ads.get("engine_list", [])
        dependency_map: dict[str, list[str]] = ads.get("dependency_map", {})
        authority_map: dict[str, str] = ads.get("authority_map", {})

        if not engine_list:
            raise RuntimeError("ADS_NO_ENGINE_LIST: architecture must name the engines involved")
        if not dependency_map:
            raise RuntimeError("ADS_NO_DEPENDENCY_MAP: must declare which engines depend on which")
        if not authority_map:
            raise RuntimeError("ADS_NO_AUTHORITY_MAP: must declare who owns state for each engine")

        # Check for engines in dependency_map not in engine_list
        ghost_deps = [e for e in dependency_map if e not in engine_list]
        if ghost_deps:
            raise RuntimeError(f"ADS_GHOST_DEPENDENCY: engines in dependency_map not in engine_list: {ghost_deps}")

        return {
            "engine_list": engine_list,
            "dependency_map": dependency_map,
            "authority_map": authority_map,
            "engine_count": len(engine_list),
            "architecture_locked": True,
        }


# ══════════════════════════════════════════════════════════════════════════════
# STAGE 7 — UXR  (User Experience Requirements)
# ══════════════════════════════════════════════════════════════════════════════
class UXR(StageBase):
    name = "UXR"

    def execute(self, state: Any) -> dict[str, Any]:
        uxr = state.task.get("uxr", {})

        constraints: list[dict[str, Any]] = uxr.get("constraints", [])
        operator = uxr.get("operator", "UNKNOWN")
        explicit_none = uxr.get("no_constraints_justification")

        if not constraints and not explicit_none:
            raise RuntimeError(
                "UXR_NO_CONSTRAINTS: must either provide user constraints " "or explicitly state no_constraints_justification"
            )

        # Each constraint must have a name and description
        for i, c in enumerate(constraints):
            if "name" not in c or "description" not in c:
                raise RuntimeError(f"UXR_INVALID_CONSTRAINT[{i}]: missing 'name' or 'description'")

        return {
            "operator": operator,
            "constraints": constraints,
            "constraint_count": len(constraints),
            "no_constraints_justified": bool(explicit_none),
        }


# ══════════════════════════════════════════════════════════════════════════════
# STAGE 8 — NUF  (Non-Functional Requirements)
# ══════════════════════════════════════════════════════════════════════════════
class NUF(StageBase):
    name = "NUF"

    VALID_CATEGORIES: set[str] = {
        "performance",
        "reliability",
        "security",
        "determinism",
        "memory",
        "latency",
        "throughput",
    }

    def execute(self, state: Any) -> dict[str, Any]:
        nuf = state.task.get("nuf", {})
        requirements: list[dict[str, Any]] = nuf.get("requirements", [])

        if not requirements:
            raise RuntimeError("NUF_NO_REQUIREMENTS: at least one non-functional requirement must be stated")

        validated: list[dict[str, Any]] = []
        for i, req in enumerate(requirements):
            if "category" not in req or "description" not in req:
                raise RuntimeError(f"NUF_INVALID_REQUIREMENT[{i}]: missing 'category' or 'description'")
            cat = req["category"]
            if cat not in self.VALID_CATEGORIES:
                raise RuntimeError(f"NUF_UNKNOWN_CATEGORY[{i}]: '{cat}' not in {self.VALID_CATEGORIES}")
            validated.append(req)

        categories_covered = {r["category"] for r in validated}

        return {
            "requirements": validated,
            "requirement_count": len(validated),
            "categories_covered": sorted(categories_covered),
        }


# ══════════════════════════════════════════════════════════════════════════════
# STAGE 9 — SSO  (System Scope Outline)
# ══════════════════════════════════════════════════════════════════════════════
class SSO(StageBase):
    name = "SSO"

    def execute(self, state: Any) -> dict[str, Any]:
        sso = state.task.get("sso", {})
        in_scope: list[str] = sso.get("in_scope", [])
        out_of_scope: list[str] = sso.get("out_of_scope", [])

        if not in_scope:
            raise RuntimeError("SSO_NO_IN_SCOPE: in_scope list cannot be empty")
        if not out_of_scope:
            raise RuntimeError(
                "SSO_NO_OUT_OF_SCOPE: must explicitly state what is out of scope. " "Empty out_of_scope is a scope creep risk."
            )

        # Check for overlap — something cannot be both in and out of scope
        overlap = set(in_scope) & set(out_of_scope)
        if overlap:
            raise RuntimeError(f"SSO_SCOPE_CONFLICT: items in both lists: {overlap}")

        return {
            "in_scope": in_scope,
            "out_of_scope": out_of_scope,
            "in_scope_count": len(in_scope),
            "out_of_scope_count": len(out_of_scope),
            "scope_locked": True,
        }


# ══════════════════════════════════════════════════════════════════════════════
# STAGE 10 — RRP  (Repair and Recovery Plan)
# ══════════════════════════════════════════════════════════════════════════════
class RRP(StageBase):
    name = "RRP"

    VALID_STRATEGIES: set[str] = {"rollback", "retry", "fallback", "halt", "escalate", "degrade"}

    def execute(self, state: Any) -> dict[str, Any]:
        rrp = state.task.get("rrp", {})
        failure_modes: list[dict[str, Any]] = rrp.get("failure_modes", [])

        if not failure_modes:
            raise RuntimeError("RRP_NO_FAILURE_MODES: at least one failure mode with recovery strategy required")

        validated: list[dict[str, Any]] = []
        for i, fm in enumerate(failure_modes):
            if "mode" not in fm:
                raise RuntimeError(f"RRP_INVALID_MODE[{i}]: missing 'mode' field")
            strategy = fm.get("strategy", "")
            if strategy not in self.VALID_STRATEGIES:
                raise RuntimeError(f"RRP_UNKNOWN_STRATEGY[{i}]: '{strategy}' not in {self.VALID_STRATEGIES}")
            if "rollback_path" not in fm and "recovery_action" not in fm:
                raise RuntimeError(f"RRP_NO_RECOVERY[{i}]: mode '{fm['mode']}' must have rollback_path or recovery_action")
            validated.append(fm)

        return {
            "failure_modes": validated,
            "failure_mode_count": len(validated),
            "strategies_used": sorted({fm["strategy"] for fm in validated}),
            "recovery_plan_locked": True,
        }


# ══════════════════════════════════════════════════════════════════════════════
# STAGE 11 — IMPLEMENTATION
# ══════════════════════════════════════════════════════════════════════════════
class IMPLEMENTATION(StageBase):
    name = "IMPLEMENTATION"

    def execute(self, state: Any) -> dict[str, Any]:
        impl = state.task.get("implementation", {})
        artifact_path = impl.get("artifact_path")
        artifact_hash = impl.get("artifact_hash")
        artifact_content = impl.get("artifact_content")

        if not artifact_path:
            raise RuntimeError("IMPLEMENTATION_NO_PATH: artifact_path required")
        if not artifact_hash:
            raise RuntimeError("IMPLEMENTATION_NO_HASH: artifact_hash required")
        if artifact_content is not None:
            actual_hash = hashlib.sha256(str(artifact_content).encode()).hexdigest()
            if actual_hash != artifact_hash:
                raise RuntimeError(f"IMPLEMENTATION_HASH_MISMATCH: " f"expected={artifact_hash[:12]} actual={actual_hash[:12]}")

        return {
            "artifact_path": artifact_path,
            "artifact_hash": artifact_hash,
            "content_verified": artifact_content is not None,
        }


# ══════════════════════════════════════════════════════════════════════════════
# STAGE 12 — VERIFICATION  (FIX: real checks against prior stages)
# ══════════════════════════════════════════════════════════════════════════════
class VERIFICATION(StageBase):
    name = "VERIFICATION"

    def execute(self, state: Any) -> dict[str, Any]:
        checks: list[str] = []
        failures: list[str] = []

        # Check 1: IMPLEMENTATION ran
        impl_data = state.data.get("IMPLEMENTATION", {})
        if not impl_data:
            failures.append("VERIFICATION_NO_IMPLEMENTATION: IMPLEMENTATION stage missing")
        else:
            checks.append("implementation_present")

        # Check 2: artifact path recorded
        impl_artifact = impl_data.get("artifact", {})
        if not impl_artifact.get("artifact_path"):
            failures.append("VERIFICATION_NO_ARTIFACT_PATH")
        else:
            checks.append("artifact_path_present")

        # Check 3: artifact hash recorded
        if not impl_artifact.get("artifact_hash"):
            failures.append("VERIFICATION_NO_ARTIFACT_HASH")
        else:
            checks.append("artifact_hash_present")

        # Check 4: CDR passed
        cdr_data = state.data.get("CDR", {})
        if not cdr_data.get("artifact", {}).get("cdr_compliant"):
            failures.append("VERIFICATION_CDR_NOT_COMPLIANT")
        else:
            checks.append("cdr_compliant")

        # Check 5: OFM success criteria exist
        ofm_data = state.data.get("OFM", {})
        if not ofm_data.get("artifact", {}).get("success_criteria"):
            failures.append("VERIFICATION_NO_SUCCESS_CRITERIA")
        else:
            checks.append("success_criteria_defined")

        # Check 6: SSO scope locked
        sso_data = state.data.get("SSO", {})
        if not sso_data.get("artifact", {}).get("scope_locked"):
            failures.append("VERIFICATION_SCOPE_NOT_LOCKED")
        else:
            checks.append("scope_locked")

        # Check 7: read-back hash match (if content available)
        impl_content = state.task.get("implementation", {}).get("artifact_content")
        expected_hash = impl_artifact.get("artifact_hash")
        if impl_content is not None and expected_hash:
            actual_hash = hashlib.sha256(str(impl_content).encode()).hexdigest()
            if actual_hash != expected_hash:
                failures.append(f"VERIFICATION_HASH_MISMATCH: " f"expected={expected_hash[:12]} actual={actual_hash[:12]}")
            else:
                checks.append("content_hash_verified")

        if failures:
            raise RuntimeError(f"VERIFICATION_FAILED: {failures}")

        return {
            "verified": True,
            "checks_passed": checks,
            "check_count": len(checks),
        }


# ══════════════════════════════════════════════════════════════════════════════
# STAGE 13 — DEBUGGING  (conditional)
# ══════════════════════════════════════════════════════════════════════════════
class DEBUGGING(StageBase):
    name = "DEBUGGING"

    def execute(self, state: Any) -> dict[str, Any]:
        debug = state.task.get("debugging", {})
        root_cause = debug.get("root_cause")
        patch_applied = debug.get("patch_applied", False)
        lesson = debug.get("lesson")

        # FIX: root_cause must not be None when DEBUGGING actually runs
        if not root_cause:
            raise RuntimeError(
                "DEBUGGING_NO_ROOT_CAUSE: root_cause must be identified and non-empty. "
                "Debugging without a root cause is symptom patching, not repair."
            )
        if not patch_applied:
            raise RuntimeError(
                "DEBUGGING_NO_PATCH: patch_applied must be True. "
                "Identifying a root cause without applying a fix is incomplete."
            )
        if not lesson:
            raise RuntimeError(
                "DEBUGGING_NO_LESSON: lesson must be written. "
                "Every debugging run must produce a lesson for the improvement loop."
            )

        return {
            "skipped": False,
            "root_cause": root_cause,
            "patch_applied": patch_applied,
            "lesson": lesson,
        }


# ══════════════════════════════════════════════════════════════════════════════
# STAGE 14 — ECL  (End Condition Lock)
# ══════════════════════════════════════════════════════════════════════════════
class ECL(StageBase):
    name = "ECL"

    def execute(self, state: Any) -> dict[str, Any]:
        ran = list(state.data.keys())
        missing = [s for s in REQUIRED_PIPELINE_STAGES if s not in ran]

        if missing:
            raise RuntimeError(f"ECL_INCOMPLETE_PIPELINE: missing stages {missing}")

        debugging_artifact = state.data.get("DEBUGGING", {}).get("artifact", {})
        debugging_skipped = debugging_artifact.get("skipped", False)
        debugging_reason = debugging_artifact.get("reason", "RAN_NORMALLY")

        return {
            "governance": "enforced",
            "stages_ran": ran,
            "stage_count": len(ran),
            "debugging_skipped": debugging_skipped,
            "debugging_reason": debugging_reason,
            "pipeline_complete": True,
        }
