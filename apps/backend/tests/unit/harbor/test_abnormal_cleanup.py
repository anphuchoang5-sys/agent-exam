import json
from dataclasses import replace
from pathlib import Path
from subprocess import CompletedProcess

import pytest
from unit.test_harbor_adapter import (
    _adapter,
    _outcome,
    _request,
    _write_json,
    _write_successful_harbor_result,
)

from eval_platform.adapters.execution.harbor import adapter as adapter_module
from eval_platform.adapters.execution.harbor.lifecycle import cleanup
from eval_platform.domain.result import TerminationReason


@pytest.mark.parametrize("returncode", [1, -9])
@pytest.mark.parametrize("cleanup_failed", [False, True])
@pytest.mark.parametrize("completed", [False, True])
def test_abnormal_exit_cleans_only_its_project_and_preserves_outcome(
    tmp_path, monkeypatch, returncode, cleanup_failed, completed
):
    project = "trial-one__env"
    resources = {
        kind: {f"target-{kind}", f"other-{kind}"}
        for kind in ("container", "network", "volume", "image")
    }
    commands = []

    def docker(command, **_kwargs):
        commands.append(command)
        assert command[0] == "docker"
        kind, operation = command[1:3]
        if operation == "ls":
            assert command[-3:] == [
                "--filter",
                f"label=com.docker.compose.project={project}",
                "--quiet",
            ]
            stdout = "\n".join(
                identity
                for identity in resources[kind]
                if identity.startswith("target-")
            )
            return CompletedProcess(command, 0, stdout, "")
        assert operation == "rm"
        assert command[-1:] == [f"target-{kind}"]
        if cleanup_failed and kind == "container":
            return CompletedProcess(command, 1, b"", b"controlled removal failure")
        resources[kind].remove(command[-1])
        return CompletedProcess(command, 0, b"", b"")

    def process(command, **kwargs):
        config_path = Path(command[3])
        config = json.loads(config_path.read_text())
        trial = Path(config["jobs_dir"]) / config["job_name"] / "trial-one"
        if completed:
            _write_successful_harbor_result(config_path)
        trial_config = {"task": config["tasks"][0], "agent": config["agents"][0]}
        _write_json(trial / "config.json", {**trial_config, "trial_name": trial.name})
        return _outcome(
            kwargs["evidence_root"],
            returncode=returncode,
            warnings=("HARBOR_STDERR_TRUNCATED",),
        )

    monkeypatch.setattr(adapter_module, "run_bounded_process", process)
    monkeypatch.setattr(cleanup.subprocess, "run", docker)

    result = _adapter(tmp_path).execute(_request())[0]

    assert commands, "Nonzero process exit skipped the project cleanup"
    assert result.termination_reason is (
        TerminationReason.COMPLETED
        if completed
        else TerminationReason.INFRASTRUCTURE_INTERRUPTED
    )
    assert "HARBOR_STDERR_TRUNCATED" in result.warnings
    assert ("HARBOR_COMPOSE_CLEANUP_FAILED" in result.warnings) is cleanup_failed
    if completed:
        assert f"HARBOR_PROCESS_EXIT_{returncode}" in result.warnings
        assert result.patch_ref is not None
    else:
        assert "HARBOR_JOB_RESULT_MISSING" in result.warnings
    for kind, identities in resources.items():
        expected = {f"other-{kind}"}
        if cleanup_failed and kind == "container":
            expected.add(f"target-{kind}")
        assert identities == expected


def test_nonzero_exit_without_trusted_trial_config_retains_unverified_cleanup(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(
        adapter_module,
        "run_bounded_process",
        lambda _command, **kwargs: _outcome(kwargs["evidence_root"], returncode=1),
    )
    result = _adapter(tmp_path).execute(_request())[0]
    assert "HARBOR_COMPOSE_CLEANUP_UNVERIFIED" in result.warnings


@pytest.mark.parametrize("start_error", [None, FileNotFoundError("not started")])
def test_success_and_process_start_failure_do_not_trigger_abnormal_cleanup(
    tmp_path, monkeypatch, start_error
):
    def process(command, **kwargs):
        if start_error is None:
            _write_successful_harbor_result(Path(command[3]))
        return replace(
            _outcome(kwargs["evidence_root"], returncode=-1 if start_error else 0),
            start_error=start_error,
        )

    def unexpected(_job_dir):
        raise AssertionError("No abnormal running process requires cleanup")

    monkeypatch.setattr(adapter_module, "run_bounded_process", process)
    monkeypatch.setattr(adapter_module, "cleanup_timed_out_projects", unexpected)
    monkeypatch.setattr(
        adapter_module, "recover_missing_codex_trajectories", lambda *_: ()
    )
    result = _adapter(tmp_path).execute(_request())[0]
    assert result.termination_reason is (
        TerminationReason.AGENT_UNAVAILABLE
        if start_error is not None
        else TerminationReason.COMPLETED
    )
