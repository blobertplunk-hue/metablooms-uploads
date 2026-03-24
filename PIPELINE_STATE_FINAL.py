from __future__ import annotations

from typing import Any


class PipelineState:
    def __init__(self, task: dict[str, Any]) -> None:
        self.task = task
        self.data: dict[str, Any] = {}
        self.history: list[dict[str, Any]] = []
        self.trace: list[dict[str, Any]] = []

    def update(self, stage_result: dict[str, Any]) -> None:
        if "stage" not in stage_result:
            raise RuntimeError("STATE_UPDATE_INVALID: missing stage")

        self.history.append(stage_result)
        self.data[stage_result["stage"]] = stage_result

        span = stage_result.get("trace_span")
        if not span:
            raise RuntimeError(f"TRACE_MISSING: {stage_result['stage']}")

        self.trace.append(span)
