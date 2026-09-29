"""Run two fixed-Harbor provider Trials concurrently and retain S11 evidence."""

from __future__ import annotations

import hashlib
import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from uuid import uuid4

from providers.runtime.s11.docker_capture import DockerCapture
from providers.runtime.s11.verdicts import require_verified, verify

from eval_platform.adapters.execution.harbor.adapter import HarborExecutionAdapter
from eval_platform.adapters.execution.harbor.config_mapper import (
    ARTIFACT_CONTRACT_VERSION,
    HARBOR_REVISION,
)
from eval_platform.adapters.tasks.swe_gym import CANDIDATE_INSTANCE_ID, SWEGymTaskSource
from eval_platform.application.ports.execution import (
    ExecutionJobRequest,
    ExecutionRunRequest,
    RunLimits,
)
from eval_platform.delivery.catalog_presets import INTERNAL_TEST_AGENT_PRESETS


def run_concurrent_trials(
    *,
    project_root: Path,
    parquet: Path,
    codex_archive: Path,
    provider_image: str,
    evidence: Path,
) -> dict:
    evidence.mkdir(parents=True, exist_ok=False)
    source = SWEGymTaskSource(parquet.resolve())
    task = source.load(CANDIDATE_INSTANCE_ID).public
    agent = next(iter(INTERNAL_TEST_AGENT_PRESETS.values()))[1]
    requests = tuple(_request(task, agent) for _ in range(2))
    scopes = tuple(_scope(request) for request in requests)
    adapter = HarborExecutionAdapter(
        project_root / "framework/harbor/.venv/Scripts/harbor.exe",
        evidence / "execution",
        project_root,
        codex_archive=codex_archive,
        provider_image_id=provider_image,
    )
    capture = DockerCapture(evidence, scopes, evidence / "execution")
    results = ()
    try:
        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = tuple(
                pool.submit(adapter.execute, request) for request in requests
            )
            capture.wait_and_capture()
            results = tuple(future.result(timeout=1000)[0] for future in futures)
    finally:
        capture.finish()
        capture.close()
    require_verified(capture.snapshot)
    summary = {
        "status": "verified",
        "scopes": scopes,
        "groups": verify(capture.snapshot),
        "trials": [
            {
                "run_id": result.run_id,
                "termination_reason": result.termination_reason.value,
                "warnings": result.warnings,
                "trajectory": result.trajectory_ref is not None,
            }
            for result in results
        ],
    }
    failed = [
        item
        for item in summary["trials"]
        if item["termination_reason"] != "completed"
        or not item["trajectory"]
        or item["warnings"]
    ]
    if failed:
        raise AssertionError(f"S11_TRIAL_RESULT_FAILED:{failed}")
    (evidence / "summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return summary


def _request(task, agent) -> ExecutionJobRequest:
    return ExecutionJobRequest(
        str(uuid4()),
        (ExecutionRunRequest(str(uuid4()), task, agent),),
        RunLimits(900, 1, 4096, 8192),
        HARBOR_REVISION,
        ARTIFACT_CONTRACT_VERSION,
    )


def _scope(request: ExecutionJobRequest) -> str:
    identity = f"{request.job_id}:{request.runs[0].run_id}".encode()
    return "t05-s10-" + hashlib.sha256(identity).hexdigest()[:20]
