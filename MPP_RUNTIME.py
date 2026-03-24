from __future__ import annotations

from typing import Any

from STAGE_RUNNER import StageRunner
from STAGES import (
    ADS,
    CDR,
    DEBUGGING,
    DRS,
    ECL,
    IMPLEMENTATION,
    MMD,
    NUF,
    OFM,
    RRP,
    SEE,
    SSO,
    UXR,
    VERIFICATION,
)


def run_mpp(task: dict[str, Any]) -> Any:
    stages = [
        SEE(),
        MMD(),
        DRS(),
        CDR(),
        OFM(),
        ADS(),
        UXR(),
        NUF(),
        SSO(),
        RRP(),
        IMPLEMENTATION(),
        VERIFICATION(),
        DEBUGGING(),
        ECL(),
    ]
    runner = StageRunner(stages)
    return runner.run(task)
