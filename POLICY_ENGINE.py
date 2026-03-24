"""
POLICY_ENGINE.py — Centralized policy evaluation (Policy-as-Code model)
========================================================================

CDR V1 (Rationale):
    CDR, VERIFICATION, and ECL each enforce policies but do so independently,
    with no shared policy registry. A policy change requires updating multiple
    stages. This engine centralizes policy definitions so all stages evaluate
    against the same source of truth. Modeled on OPA/Rego pattern:
    Input → Policy Evaluation → Decision → Enforcement → Audit.

CDR V2 (Trust):
    Policies are registered at startup. evaluate() is pure — same input
    always produces same decision. No side effects during evaluation.

CDR V3 (Boundary):
    Receives a policy_name and context dict. Returns PolicyDecision.
    Does not modify state. Does not run stages. Consumers own enforcement.

CDR V4 (Failure):
    Unknown policy name → DENY with explanation. Never silently passes
    an unknown policy as compliant.

Integration contract:
    Inputs:  policy_name (str), context (dict)
    Outputs: PolicyDecision(allowed, policy_name, reason, violations)
    Side effects: none
    Assumptions: called by CDR, VERIFICATION, ECL before their own checks
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any


@dataclass
class PolicyDecision:
    allowed: bool
    policy_name: str
    reason: str
    violations: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "allowed": self.allowed,
            "policy_name": self.policy_name,
            "reason": self.reason,
            "violations": self.violations,
        }


# Policy type: takes context dict, returns (allowed, violations)
PolicyFn = Callable[[dict[str, Any]], tuple[bool, list[str]]]


class PolicyEngine:
    """
    Central policy registry and evaluator.

    Usage:
        engine = PolicyEngine()
        decision = engine.evaluate("cdr_attestation", {"attestation": "..."})
        if not decision.allowed:
            raise RuntimeError(decision.reason)
    """

    def __init__(self) -> None:
        self._policies: dict[str, PolicyFn] = {}
        self._register_defaults()

    def register(self, name: str, fn: PolicyFn) -> None:
        """Register a named policy function."""
        self._policies[name] = fn

    def evaluate(self, policy_name: str, context: dict[str, Any]) -> PolicyDecision:
        """Evaluate a named policy against a context. Fail closed on unknown policy."""
        fn = self._policies.get(policy_name)
        if fn is None:
            return PolicyDecision(
                allowed=False,
                policy_name=policy_name,
                reason=f"POLICY_UNKNOWN: '{policy_name}' not registered — fail closed",
                violations=[f"unregistered policy: {policy_name}"],
            )
        allowed, violations = fn(context)
        reason = "POLICY_PASS" if allowed else f"POLICY_DENY: {violations}"
        return PolicyDecision(
            allowed=allowed,
            policy_name=policy_name,
            reason=reason,
            violations=violations,
        )

    def _register_defaults(self) -> None:
        """Register the canonical MetaBlooms governance policies."""

        # P-001: CDR attestation required
        def p_cdr_attestation(ctx: dict[str, Any]) -> tuple[bool, list[str]]:
            attestation = ctx.get("attestation")
            if not attestation or len(str(attestation)) < 10:
                return False, ["CDR_P001: attestation missing or too brief"]
            return True, []

        # P-002: No junk-drawer module names
        CDR_FORBIDDEN = {"utils", "helpers", "misc", "tools", "common", "stuff"}

        def p_module_naming(ctx: dict[str, Any]) -> tuple[bool, list[str]]:
            name = ctx.get("module_name", "")
            base = name.lower().replace(".py", "").replace("_engine", "").replace("_final", "")
            if base in CDR_FORBIDDEN:
                return False, [f"CDR_P002: forbidden module name '{name}'"]
            return True, []

        # P-003: Implementation artifact must have hash
        def p_artifact_integrity(ctx: dict[str, Any]) -> tuple[bool, list[str]]:
            violations = []
            if not ctx.get("artifact_path"):
                violations.append("CDR_P003: artifact_path missing")
            if not ctx.get("artifact_hash"):
                violations.append("CDR_P003: artifact_hash missing")
            return len(violations) == 0, violations

        # P-004: Pipeline must have run all mandatory stages
        MANDATORY = {"SEE", "CDR", "IMPLEMENTATION", "VERIFICATION", "ECL"}

        def p_mandatory_stages(ctx: dict[str, Any]) -> tuple[bool, list[str]]:
            ran = set(ctx.get("stages_ran", []))
            missing = MANDATORY - ran
            if missing:
                return False, [f"CDR_P004: mandatory stages not run: {sorted(missing)}"]
            return True, []

        # P-005: SEE evidence must meet minimum count
        def p_evidence_minimum(ctx: dict[str, Any]) -> tuple[bool, list[str]]:
            count = ctx.get("evidence_count", 0)
            if count < 3:
                return False, [f"CDR_P005: evidence_count={count} < 3 required"]
            return True, []

        # P-006: RRP must exist before IMPLEMENTATION
        def p_recovery_before_impl(ctx: dict[str, Any]) -> tuple[bool, list[str]]:
            has_rrp = ctx.get("rrp_complete", False)
            if not has_rrp:
                return False, ["CDR_P006: RRP must be complete before IMPLEMENTATION"]
            return True, []

        self.register("cdr_attestation", p_cdr_attestation)
        self.register("module_naming", p_module_naming)
        self.register("artifact_integrity", p_artifact_integrity)
        self.register("mandatory_stages", p_mandatory_stages)
        self.register("evidence_minimum", p_evidence_minimum)
        self.register("recovery_before_impl", p_recovery_before_impl)


# Module-level singleton for use by stages
_DEFAULT_ENGINE = PolicyEngine()


def evaluate_policy(policy_name: str, context: dict[str, Any]) -> PolicyDecision:
    """Convenience function using the default engine singleton."""
    return _DEFAULT_ENGINE.evaluate(policy_name, context)
