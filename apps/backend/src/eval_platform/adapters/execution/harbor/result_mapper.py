from __future__ import annotations

import hashlib
import json
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from eval_platform.adapters.execution.harbor.artifacts import (
    PatchArtifactError,
    validate_patch_artifact,
)
from eval_platform.adapters.execution.harbor.config_mapper import (
    HarborJobPlan,
    harbor_agent_key,
    harbor_task_path_key,
)
from eval_platform.domain.result import (
    ArtifactRef,
    ExecutionTrialResult,
    ResourceSummary,
    TerminationReason,
    UsageSummary,
)

_RAW_ARTIFACT_MAX_BYTES = 50 * 1024 * 1024


def map_job_results(
    plan: HarborJobPlan,
    job_dir: Path,
    *,
    process_returncode: int,
) -> tuple[ExecutionTrialResult, ...]:
    try:
        job_data = _read_json(job_dir / "result.json")
        job_ref = _required_string(job_data, "id")
    except (OSError, ValueError, json.JSONDecodeError):
        return _missing_results(
            plan,
            str(job_dir.resolve()),
            TerminationReason.INFRASTRUCTURE_INTERRUPTED,
            "HARBOR_JOB_RESULT_MISSING",
        )

    bindings = {
        (binding.task_path_key, binding.agent_key): binding
        for binding in plan.bindings
    }
    mapped: dict[str, ExecutionTrialResult] = {}
    protocol_warnings: list[str] = []
    for result_path in sorted(job_dir.glob("*/result.json")):
        try:
            trial_data = _read_json(result_path)
            key = _trial_key(trial_data)
            binding = bindings.get(key)
            if binding is None:
                protocol_warnings.append("UNEXPECTED_HARBOR_TRIAL")
                continue
            if binding.run_id in mapped:
                protocol_warnings.append("DUPLICATE_HARBOR_TRIAL")
                continue
            mapped[binding.run_id] = _map_trial(
                run_id=binding.run_id,
                job_ref=job_ref,
                trial_dir=result_path.parent,
                trial_data=trial_data,
                process_returncode=process_returncode,
            )
        except (OSError, ValueError, json.JSONDecodeError):
            protocol_warnings.append("INVALID_HARBOR_TRIAL_RESULT")

    results: list[ExecutionTrialResult] = []
    for binding in plan.bindings:
        result = mapped.get(binding.run_id)
        if result is None:
            reason = (
                TerminationReason.BACKEND_PROTOCOL_ERROR
                if process_returncode == 0
                else TerminationReason.INFRASTRUCTURE_INTERRUPTED
            )
            result = _failed_result(
                binding.run_id,
                job_ref,
                reason,
                "HARBOR_TRIAL_RESULT_MISSING",
            )
        if protocol_warnings:
            result = replace(
                result,
                warnings=(*result.warnings, *dict.fromkeys(protocol_warnings)),
            )
        results.append(result)
    return tuple(results)


def _trial_key(data: dict[str, Any]) -> tuple[str, str]:
    config = _required_mapping(data, "config")
    task = _required_mapping(config, "task")
    agent = _required_mapping(config, "agent")
    return (
        harbor_task_path_key(_required_string(task, "path")),
        harbor_agent_key(agent),
    )


def _map_trial(
    *,
    run_id: str,
    job_ref: str,
    trial_dir: Path,
    trial_data: dict[str, Any],
    process_returncode: int,
) -> ExecutionTrialResult:
    trial_ref = _required_string(trial_data, "id")
    warnings: list[str] = []
    raw_config_ref = _file_ref(
        trial_dir / "config.json", "harbor_trial_config", "application/json"
    )
    raw_result_ref = _file_ref(
        trial_dir / "result.json", "harbor_trial_result", "application/json"
    )
    exception = trial_data.get("exception_info")
    if isinstance(exception, dict):
        reason = _exception_reason(str(exception.get("exception_type", "")))
        patch_ref = None
    else:
        try:
            patch = validate_patch_artifact(trial_dir / "artifacts/agentexam")
            patch_ref = ArtifactRef(
                object_key=str(
                    (trial_dir / "artifacts/agentexam/model.patch").resolve()
                ),
                artifact_type="model_patch",
                size_bytes=patch.size_bytes,
                sha256=patch.sha256,
                content_type="text/x-diff",
                created_at=_modified_at(
                    trial_dir / "artifacts/agentexam/model.patch"
                ),
                warnings=patch.warnings,
            )
            reason = TerminationReason.COMPLETED
        except PatchArtifactError as exc:
            patch_ref = None
            reason = _patch_error_reason(exc.code)
            warnings.append(exc.code)

    trajectory_ref = _optional_file_ref(
        trial_dir / "agent/trajectory.json",
        "agent_trajectory",
        "application/json",
    )
    if trajectory_ref is None:
        warnings.append("TRAJECTORY_UNAVAILABLE")
    if process_returncode != 0:
        warnings.append(f"HARBOR_PROCESS_EXIT_{process_returncode}")
    return ExecutionTrialResult(
        run_id=run_id,
        backend_job_ref=job_ref,
        backend_trial_ref=trial_ref,
        termination_reason=reason,
        patch_ref=patch_ref,
        trajectory_ref=trajectory_ref,
        raw_config_ref=raw_config_ref,
        raw_result_ref=raw_result_ref,
        usage=_usage(trial_data.get("agent_result")),
        resource_summary=_resources(trial_data),
        warnings=tuple(warnings),
    )


def _file_ref(path: Path, artifact_type: str, content_type: str) -> ArtifactRef:
    if not path.is_file() or path.is_symlink():
        raise ValueError(f"Required Harbor artifact is missing: {path.name}")
    content = path.read_bytes()
    return ArtifactRef(
        object_key=str(path.resolve()),
        artifact_type=artifact_type,
        size_bytes=len(content),
        sha256=hashlib.sha256(content).hexdigest(),
        content_type=content_type,
        created_at=_modified_at(path),
    )


def _optional_file_ref(
    path: Path, artifact_type: str, content_type: str
) -> ArtifactRef | None:
    if not path.is_file() or path.is_symlink():
        return None
    if path.stat().st_size > _RAW_ARTIFACT_MAX_BYTES:
        return None
    return _file_ref(path, artifact_type, content_type)


def _usage(value: Any) -> UsageSummary | None:
    if not isinstance(value, dict):
        return None
    summary = UsageSummary(
        n_input_tokens=value.get("n_input_tokens"),
        n_cache_tokens=value.get("n_cache_tokens"),
        n_output_tokens=value.get("n_output_tokens"),
        cost_usd=value.get("cost_usd"),
    )
    return summary if any(value is not None for value in summary.__dict__.values()) else None


def _resources(data: dict[str, Any]) -> ResourceSummary | None:
    started = _parse_datetime(data.get("started_at"))
    finished = _parse_datetime(data.get("finished_at"))
    if started is None or finished is None:
        return None
    return ResourceSummary(wall_time_sec=max(0.0, (finished - started).total_seconds()))


def _parse_datetime(value: Any) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _modified_at(path: Path) -> datetime:
    return datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)


def _exception_reason(exception_type: str) -> TerminationReason:
    if exception_type in {"AgentAuthenticationError", "ApiUsageLimitError", "ModelNotFoundError"}:
        return TerminationReason.AGENT_UNAVAILABLE
    if "Timeout" in exception_type:
        return TerminationReason.TIMED_OUT
    if "Environment" in exception_type or "Docker" in exception_type:
        return TerminationReason.SANDBOX_FAILED
    return TerminationReason.AGENT_FAILED


def _patch_error_reason(code: str) -> TerminationReason:
    if code == "PATCH_TOO_LARGE":
        return TerminationReason.PATCH_TOO_LARGE
    if code == "BINARY_PATCH_NOT_ALLOWED":
        return TerminationReason.BINARY_PATCH_NOT_ALLOWED
    return TerminationReason.PATCH_EXTRACTION_FAILED


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("Harbor JSON root must be an object")
    return value


def _required_mapping(data: dict[str, Any], key: str) -> dict[str, Any]:
    value = data.get(key)
    if not isinstance(value, dict):
        raise ValueError(f"Harbor result has no {key} object")
    return value


def _required_string(data: dict[str, Any], key: str) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value:
        raise ValueError(f"Harbor result has no {key} string")
    return value


def _missing_results(
    plan: HarborJobPlan,
    job_ref: str,
    reason: TerminationReason,
    warning: str,
) -> tuple[ExecutionTrialResult, ...]:
    return tuple(
        _failed_result(binding.run_id, job_ref, reason, warning)
        for binding in plan.bindings
    )


def _failed_result(
    run_id: str,
    job_ref: str,
    reason: TerminationReason,
    warning: str,
) -> ExecutionTrialResult:
    return ExecutionTrialResult(
        run_id=run_id,
        backend_job_ref=job_ref,
        backend_trial_ref="",
        termination_reason=reason,
        patch_ref=None,
        trajectory_ref=None,
        warnings=(warning,),
    )
