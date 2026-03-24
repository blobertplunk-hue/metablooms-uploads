from __future__ import annotations

import copy

from PIPELINE_STATE_FINAL import PipelineState

MAX_DEBUG_LOOPS: int = 2


class StageRunner:
    def __init__(self, stages: list) -> None:
        self.stages = stages

    def run(self, task: dict) -> PipelineState:
        state = PipelineState(copy.deepcopy(task))

        for stage in self.stages:
            # DEBUGGING is conditional on VERIFICATION result
            if stage.name == "DEBUGGING":
                verification = state.data.get("VERIFICATION", {})
                verified = verification.get("artifact", {}).get("verified", False)
                if verified:
                    skipped_result = {
                        "stage": "DEBUGGING",
                        "status": "COMPLETE",
                        "artifact": {"skipped": True, "reason": "VERIFICATION_PASSED"},
                        "trace_span": {
                            "stage": "DEBUGGING",
                            "artifacts": {"skipped": True},
                        },
                    }
                    state.update(skipped_result)
                    continue

            result = stage.run(state)

            if result["status"] != "COMPLETE":
                raise RuntimeError(f"STAGE_FAIL: {stage.name}")

            state.update(result)

        return state
