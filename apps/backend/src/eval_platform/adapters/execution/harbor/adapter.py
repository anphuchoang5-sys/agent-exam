from __future__ import annotations

import json
import os
import subprocess
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from eval_platform.adapters.execution.harbor.config_mapper import (
    HarborJobPlan,
    build_job_plan,
    validate_job_id,
)
from eval_platform.adapters.execution.harbor.result_mapper import map_job_results
from eval_platform.adapters.tasks.swe_gym import render_harbor_task
from eval_platform.application.ports.execution import (
    ExecutionJobRequest,
    RunLimits,
)
from eval_platform.domain.result import ExecutionTrialResult, TerminationReason
from eval_platform.domain.task import EvaluationTask

TaskRenderer = Callable[[EvaluationTask, Path, RunLimits], Path]
_ENVIRONMENT_BUILD_TIMEOUT_SEC = 1800
_AGENT_SETUP_TIMEOUT_SEC = 360
_COLLECT_TIMEOUT_SEC = 60
_PROCESS_GRACE_SEC = 120
_TIMEOUT_EXIT_CODE = 124


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
        try:
            completed = subprocess.run(
                command,
                cwd=self.project_root.resolve(),
                env=env,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=_process_timeout_sec(request),
                check=False,
            )
        except subprocess.TimeoutExpired as error:
            _write_process_logs(run_root, error.stdout, error.stderr)
            return map_job_results(
                plan,
                _job_dir(plan, request.job_id),
                process_returncode=_TIMEOUT_EXIT_CODE,
                process_failure_reason=TerminationReason.TIMED_OUT,
                process_warning="HARBOR_PROCESS_TIMEOUT",
            )
        except OSError as error:
            _write_process_logs(run_root, "", f"{type(error).__name__}: {error}")
            return _process_start_failure(request, run_root, error)

        _write_process_logs(run_root, completed.stdout, completed.stderr)
        return map_job_results(
            plan,
            _job_dir(plan, request.job_id),
            process_returncode=completed.returncode,
        )


def _process_timeout_sec(request: ExecutionJobRequest) -> int:
    per_trial = (
        _ENVIRONMENT_BUILD_TIMEOUT_SEC
        + _AGENT_SETUP_TIMEOUT_SEC
        + request.limits.wall_timeout_sec
        + _COLLECT_TIMEOUT_SEC
        + _PROCESS_GRACE_SEC
    )
    return len(request.runs) * per_trial


def _job_dir(plan: HarborJobPlan, job_id: str) -> Path:
    return Path(str(plan.config["jobs_dir"])) / job_id


def _write_process_logs(
    run_root: Path, stdout: str | bytes | None, stderr: str | bytes | None
) -> None:
    (run_root / "harbor.stdout.log").write_text(
        _output_text(stdout), encoding="utf-8", newline="\n"
    )
    (run_root / "harbor.stderr.log").write_text(
        _output_text(stderr), encoding="utf-8", newline="\n"
    )


def _output_text(value: str | bytes | None) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value


def _process_start_failure(
    request: ExecutionJobRequest,
    run_root: Path,
    error: OSError,
) -> tuple[ExecutionTrialResult, ...]:
    reason = (
        TerminationReason.AGENT_UNAVAILABLE
        if isinstance(error, FileNotFoundError)
        else TerminationReason.INFRASTRUCTURE_INTERRUPTED
    )
    return tuple(
        ExecutionTrialResult(
            run_id=run.run_id,
            backend_job_ref=str((run_root / "jobs" / request.job_id).resolve()),
            backend_trial_ref="",
            termination_reason=reason,
            patch_ref=None,
            trajectory_ref=None,
            warnings=("HARBOR_PROCESS_START_FAILED",),
        )
        for run in request.runs
    )
