from __future__ import annotations

import json
from pathlib import Path
from subprocess import CompletedProcess

from eval_platform.adapters.execution.harbor.recovery.trajectory import (
    _RECOVERY_SCRIPT,
    _child_path,
    recover_missing_codex_trajectories,
)


def _trial(job_dir: Path, *, trajectory: bool = False) -> Path:
    agent_dir = job_dir / "trial-one/agent"
    session = agent_dir / "sessions/2026/09/23/rollout.jsonl"
    session.parent.mkdir(parents=True)
    session.write_text('{"type":"session_meta","payload":{"id":"one"}}\n')
    if trajectory:
        (agent_dir / "trajectory.json").write_text("{}", encoding="utf-8")
    return agent_dir


def test_recovery_script_is_valid_python() -> None:
    compile(_RECOVERY_SCRIPT, "<harbor-trajectory-recovery>", "exec")


def test_windows_child_uses_an_extended_path(tmp_path: Path) -> None:
    assert _child_path(tmp_path, platform="nt") == "\\\\?\\" + str(tmp_path.resolve())


def test_recovers_a_missing_trajectory_with_the_fixed_harbor_python(
    tmp_path: Path,
) -> None:
    job_dir = tmp_path / "jobs/job-one"
    agent_dir = _trial(job_dir)
    executable = tmp_path / "harbor.exe"
    executable.touch()
    python = tmp_path / "python.exe"
    python.touch()
    calls: list[list[str]] = []

    def run(command, **_kwargs):
        calls.append(command)
        Path(command[-1], "trajectory.json").write_text(
            json.dumps({"schema_version": "ATIF-v1.7"}), encoding="utf-8"
        )
        return CompletedProcess(command, 0)

    warnings = recover_missing_codex_trajectories(
        executable,
        job_dir,
        run_process=run,
        timeout_sec=0.1,
        pause=lambda _seconds: None,
    )

    assert warnings == ()
    assert calls == [[str(python.resolve()), "-c", calls[0][2], _child_path(agent_dir)]]
    assert (agent_dir / "trajectory.json").is_file()


def test_existing_trajectory_never_starts_a_recovery_process(tmp_path: Path) -> None:
    job_dir = tmp_path / "jobs/job-one"
    _trial(job_dir, trajectory=True)
    executable = tmp_path / "harbor.exe"
    executable.touch()
    executable.with_name("python.exe").touch()

    def unexpected(*_args, **_kwargs):
        raise AssertionError("recovery process must not start")

    warnings = recover_missing_codex_trajectories(
        executable, job_dir, run_process=unexpected
    )

    assert warnings == ()


def test_failed_recovery_is_a_stable_warning(tmp_path: Path) -> None:
    job_dir = tmp_path / "jobs/job-one"
    _trial(job_dir)
    executable = tmp_path / "harbor.exe"
    executable.touch()
    executable.with_name("python.exe").touch()

    warnings = recover_missing_codex_trajectories(
        executable,
        job_dir,
        run_process=lambda command, **_kwargs: CompletedProcess(command, 3),
        timeout_sec=0.1,
        pause=lambda _seconds: None,
    )

    assert warnings == ("HARBOR_TRAJECTORY_RECOVERY_FAILED",)
