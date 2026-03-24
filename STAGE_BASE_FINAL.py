from __future__ import annotations

from typing import Any


class StageBase:
    name: str = "BASE"

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        # Only enforce on concrete classes (not intermediate abstracts)
        if "execute" in cls.__dict__ and cls.name == "BASE":
            raise TypeError(
                f"{cls.__name__} must define class attribute 'name' — "
                f"do not inherit the default 'BASE' value"
            )

    def validate_input(self, state: Any) -> None:
        if state is None:
            raise RuntimeError(f"{self.name}_INPUT_INVALID")

    def validate_output(self, result: dict[str, Any]) -> None:
        required = ["stage", "status", "artifact", "trace_span"]
        for key in required:
            if key not in result:
                raise RuntimeError(f"{self.name}_OUTPUT_INVALID: missing {key}")
        if result["status"] != "COMPLETE":
            raise RuntimeError(f"{self.name}_NOT_COMPLETE")

    def execute(self, state: Any) -> dict[str, Any]:
        raise NotImplementedError

    def run(self, state: Any) -> dict[str, Any]:
        self.validate_input(state)
        artifact = self.execute(state)
        result = {
            "stage": self.name,
            "status": "COMPLETE",
            "artifact": artifact,
            "trace_span": {"stage": self.name, "artifacts": artifact},
        }
        self.validate_output(result)
        return result
