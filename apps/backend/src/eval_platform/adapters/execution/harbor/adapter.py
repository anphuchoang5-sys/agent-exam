from __future__ import annotations

import json
import os
import re
import subprocess
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from eval_platform.adapters.execution.harbor.config_mapper import (
    HarborJobPlan,
    build_job_plan,
    process_timeout_sec,
    validate_job_id,
)
from eval_platform.adapters.execution.harbor.process_runner import run_bounded_process
from eval_platform.adapters.execution.harbor.result_mapper import map_job_results
from eval_platform.adapters.execution.harbor.result_values import process_start_failure
from eval_platform.adapters.tasks.swe_gym import render_harbor_task
from eval_platform.application.ports.execution import (
    ExecutionJobRequest,
    RunLimits,
)
from eval_platform.domain.result import ExecutionTrialResult, TerminationReason
from eval_platform.domain.task import EvaluationTask

TaskRenderer = Callable[[EvaluationTask, Path, RunLimits], Path]
_DOCKER_TIMEOUT_SEC = 30
_COMPOSE_RESOURCES = (
    (["container", "ls", "--all"], ["container", "rm", "--force"]),
    (["network", "ls"], ["network", "rm"]),
    (["volume", "ls"], ["volume", "rm", "--force"]),
    (["image", "ls"], ["image", "rm"]),
)


@dataclass(frozen=True, slots=True)
class HarborExecutionAdapter:
    harbor_executable: Path
    evidence_root: Path
    project_root: Path
    task_renderer: TaskRenderer = render_harbor_task

    def __post_init__(self) -> None:
        if not self.harbor_executable.is_file() or self.harbor_executable.is_symlink():
            raise FileNotFoundError("The fixed Harbor executable is unavailable")
        if not self.project_root.is_dir():
            raise NotADirectoryError("The Harbor project root is unavailable")

    def execute(self, request: ExecutionJobRequest) -> tuple[ExecutionTrialResult, ...]:
        validate_job_id(request.job_id)
        run_root = self.evidence_root.resolve() / request.job_id
        if run_root.exists():
            raise FileExistsError(
                f"Refusing to overwrite execution evidence: {run_root}"
            )
        run_root.mkdir(parents=True)
        task_dirs = self._render_tasks(request, run_root / "tasks")
        plan = build_job_plan(
            request,
            jobs_dir=run_root / "jobs",
            task_dirs=task_dirs,
        )
        config_path = run_root / "harbor-config.json"
        config_path.write_text(
            json.dumps(plan.config, indent=2, sort_keys=True),
            encoding="utf-8",
            newline="\n",
        )
        return self._run(plan, request, run_root, config_path)

    def _render_tasks(
        self,
        request: ExecutionJobRequest,
        root: Path,
    ) -> dict[str, Path]:
        tasks: dict[str, EvaluationTask] = {}
        rendered: dict[str, Path] = {}
        for run in request.runs:
            previous = tasks.get(run.task.instance_id)
            if previous is not None and previous != run.task:
                raise ValueError("A task identity maps to conflicting snapshots")
            if previous is None:
                tasks[run.task.instance_id] = run.task
                rendered[run.task.instance_id] = self.task_renderer(
                    run.task, root, request.limits
                )
        return rendered

    def _run(
        self,
        plan: HarborJobPlan,
        request: ExecutionJobRequest,
        run_root: Path,
        config_path: Path,
    ) -> tuple[ExecutionTrialResult, ...]:
        env = os.environ.copy()
        env.update(
            {
                "HARBOR_TELEMETRY": "disabled",
                "PYTHONIOENCODING": "utf-8",
                "PYTHONUTF8": "1",
            }
        )
        command = [
            str(self.harbor_executable.resolve()),
            "run",
            "--config",
            str(config_path.resolve()),
            "--yes",
        ]
        outcome = run_bounded_process(
            command,
            cwd=self.project_root.resolve(),
            env=env,
            timeout_sec=process_timeout_sec(request),
            evidence_root=run_root,
        )
        if outcome.start_error is not None:
            return process_start_failure(
                request, run_root, outcome.start_error, outcome.warnings
            )
        process_warnings = outcome.warnings
        if outcome.timed_out:
            process_warnings += _cleanup_timed_out_projects(
                _job_dir(plan, request.job_id)
            )
        return map_job_results(
            plan,
            _job_dir(plan, request.job_id),
            process_returncode=outcome.returncode,
            process_failure_reason=(
                TerminationReason.TIMED_OUT if outcome.timed_out else None
            ),
            process_warnings=process_warnings,
        )


def _job_dir(plan: HarborJobPlan, job_id: str) -> Path:
    return Path(str(plan.config["jobs_dir"])) / job_id


def _cleanup_timed_out_projects(job_dir: Path) -> tuple[str, ...]:
    configs = sorted(job_dir.glob("*/config.json"))
    if not configs:
        return ("HARBOR_COMPOSE_CLEANUP_UNVERIFIED",)
    failed = False
    for path in configs:
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
            trial_name = value.get("trial_name")
            if not isinstance(trial_name, str) or trial_name != path.parent.name:
                raise ValueError("Untrusted Harbor Trial identity")
            project = re.sub(r"[^a-z0-9_-]", "-", f"{trial_name}__env".lower())
            for list_args, remove_args in _COMPOSE_RESOURCES:
                ids = _docker_resource_ids(list_args, project)
                if ids:
                    removed = subprocess.run(
                        ["docker", *remove_args, *ids],
                        capture_output=True,
                        timeout=_DOCKER_TIMEOUT_SEC,
                        check=False,
                    )
                    failed |= removed.returncode != 0
                failed |= bool(_docker_resource_ids(list_args, project))
        except (OSError, RuntimeError, subprocess.SubprocessError, ValueError):
            failed = True
    return ("HARBOR_COMPOSE_CLEANUP_FAILED",) if failed else ()


def _docker_resource_ids(list_args: list[str], project: str) -> tuple[str, ...]:
    result = subprocess.run(
        [
            "docker",
            *list_args,
            "--filter",
            f"label=com.docker.compose.project={project}",
            "--quiet",
        ],
        capture_output=True,
        text=True,
        timeout=_DOCKER_TIMEOUT_SEC,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError("Docker resource query failed")
    return tuple(dict.fromkeys(result.stdout.split()))
