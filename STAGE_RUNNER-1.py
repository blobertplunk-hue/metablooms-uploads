from __future__ import annotations

import copy
from typing import Any

from PIPELINE_STATE import PipelineState

MAX_DEBUG_LOOPS: int = 2


class StageRunner:
    def __init__(self, stages: list) -> None:
        self.stages = stages

    def run(self, task: dict[str, Any]) -> PipelineState:
        state = PipelineState(copy.deepcopy(task))
        for stage in self.stages:
            if stage.name == "DEBUGGING":
                verification = state.data.get("VERIFICATION", {})
                verified = verification.get("artifact", {}).get("verified", False)
                if verified:
                    state.update(
                        {
                            "stage": "DEBUGGING",
                            "status": "COMPLETE",
                            "artifact": {"skipped": True, "reason": "VERIFICATION_PASSED"},
                            "trace_span": {"stage": "DEBUGGING", "artifacts": {"skipped": True}},
                        }
                    )
                    continue
            result = stage.run(state)
            if result["status"] != "COMPLETE":
                raise RuntimeError(f"STAGE_FAIL: {stage.name}")
            state.update(result)
        return state
