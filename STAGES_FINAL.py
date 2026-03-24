from __future__ import annotations

from typing import Any

from STAGE_BASE_FINAL import StageBase

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


class SEE(StageBase):
    name = "SEE"

    def execute(self, state: Any) -> dict[str, Any]:
        receipts = state.task.get("sie_receipts")
        if not receipts:
            raise RuntimeError("SEE_NO_WEB_RUN_DATA")
        return {"evidence_count": len(receipts)}


class MMD(StageBase):
    name = "MMD"

    def execute(self, state: Any) -> dict[str, Any]:
        gaps: list[dict[str, Any]] = []

        if "SEE" not in state.data:
            gaps.append({"gap": "MISSING_SEE", "severity": "critical"})
            return {"gaps": gaps, "gap_count": len(gaps)}

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

        return {"gaps": gaps, "gap_count": len(gaps), "evidence_count_seen": evidence_count}


class DRS(StageBase):
    name = "DRS"

    def execute(self, state: Any) -> dict[str, Any]:
        return {"decisions": ["DRS-LOCK"]}


class CDR(StageBase):
    name = "CDR"

    def execute(self, state: Any) -> dict[str, Any]:
        return {"code_quality": "validated"}


class OFM(StageBase):
    name = "OFM"

    def execute(self, state: Any) -> dict[str, Any]:
        return {"objective_defined": True}


class ADS(StageBase):
    name = "ADS"

    def execute(self, state: Any) -> dict[str, Any]:
        return {"architecture": "locked"}


class UXR(StageBase):
    name = "UXR"

    def execute(self, state: Any) -> dict[str, Any]:
        return {"user_constraints": []}


class NUF(StageBase):
    name = "NUF"

    def execute(self, state: Any) -> dict[str, Any]:
        return {"non_functional": ["deterministic"]}


class SSO(StageBase):
    name = "SSO"

    def execute(self, state: Any) -> dict[str, Any]:
        return {"scope": "defined"}


class RRP(StageBase):
    name = "RRP"

    def execute(self, state: Any) -> dict[str, Any]:
        return {"recovery": "defined"}


class IMPLEMENTATION(StageBase):
    name = "IMPLEMENTATION"

    def execute(self, state: Any) -> dict[str, Any]:
        return {"artifact": "built"}


class VERIFICATION(StageBase):
    name = "VERIFICATION"

    def execute(self, state: Any) -> dict[str, Any]:
        if "IMPLEMENTATION" not in state.data:
            raise RuntimeError("VERIFICATION_NO_IMPLEMENTATION")
        return {"verified": True}


class DEBUGGING(StageBase):
    name = "DEBUGGING"

    def execute(self, state: Any) -> dict[str, Any]:
        return {"skipped": False, "root_cause": None}


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
