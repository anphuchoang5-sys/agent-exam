from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from eval_platform.application.ports.execution import ExecutionJobRequest
from eval_platform.domain.agent import AgentConfiguration

HARBOR_REVISION = "6af8d6e31eced13b93849cdf80feeadf24603d15"
ARTIFACT_CONTRACT_VERSION = "agentexam.m0.v1"
_SAFE_ID = re.compile(r"[a-zA-Z0-9][a-zA-Z0-9._-]{0,63}")


@dataclass(frozen=True, slots=True)
class HarborJobPlan:
    config: dict[str, Any]
    run_ids: tuple[str, ...]


def build_job_plan(
    request: ExecutionJobRequest,
    *,
    jobs_dir: Path,
    task_dirs: Mapping[str, Path],
) -> HarborJobPlan:
    if request.backend_revision != HARBOR_REVISION:
        raise ValueError("Harbor revision is not registered")
    if request.artifact_contract_version != ARTIFACT_CONTRACT_VERSION:
        raise ValueError("Harbor artifact contract is not supported")
    if not _SAFE_ID.fullmatch(request.job_id):
        raise ValueError("job_id is not safe for a Harbor job name")
    agents: dict[str, dict[str, Any]] = {}
    tasks: dict[str, dict[str, str]] = {}
    for run in request.runs:
        agents.setdefault(run.agent.fingerprint, _map_agent(run.agent))
        task_dir = task_dirs.get(run.task.instance_id)
        if task_dir is None:
            raise ValueError(f"No rendered Harbor task for {run.task.instance_id}")
        tasks.setdefault(run.task.instance_id, {"path": str(task_dir.resolve())})
    limits = request.limits
    config: dict[str, Any] = {
        "job_name": request.job_id,
        "jobs_dir": str(jobs_dir.resolve()),
        "n_attempts": 1,
        "n_concurrent_trials": 1,
        "quiet": False,
        "retry": {"max_retries": 0},
        "environment": {
            "type": "docker",
            "delete": True,
            "force_build": False,
            "cpu_enforcement_policy": "limit",
            "memory_enforcement_policy": "limit",
            "override_cpus": limits.cpus,
            "override_memory_mb": limits.memory_mb,
            "override_storage_mb": limits.storage_mb,
        },
        "verifier": {"disable": True},
        "agents": list(agents.values()),
        "tasks": list(tasks.values()),
    }
    return HarborJobPlan(
        config=config, run_ids=tuple(run.run_id for run in request.runs)
    )


def _map_agent(agent: AgentConfiguration) -> dict[str, Any]:
    if agent.agent_name != "codex":
        raise ValueError("M0 only permits the registered Codex Agent")
    allowed = {"reasoning_effort"}
    unknown = set(agent.critical_config) - allowed
    if unknown:
        raise ValueError(f"Unsupported Codex critical config: {sorted(unknown)}")
    effort = agent.critical_config.get("reasoning_effort")
    if effort not in {"low", "medium", "high", "xhigh"}:
        raise ValueError("Codex reasoning_effort must be explicitly registered")
    return {
        "name": "codex",
        "model_name": f"{agent.model_provider}/{agent.model_name}",
        "n_concurrent": 1,
        "kwargs": {
            "version": agent.agent_version,
            "reasoning_effort": effort,
            "web_search": "disabled",
        },
    }
