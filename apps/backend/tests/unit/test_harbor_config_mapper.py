from __future__ import annotations

import json
from pathlib import Path

import pytest

from eval_platform.adapters.execution.harbor.config_mapper import (
    ARTIFACT_CONTRACT_VERSION,
    HARBOR_REVISION,
    build_job_plan,
)
from eval_platform.application.ports.execution import (
    ExecutionJobRequest,
    ExecutionRunRequest,
    RunLimits,
)
from eval_platform.domain.agent import AgentConfiguration
from eval_platform.domain.task import EvaluationTask


def _agent() -> AgentConfiguration:
    return AgentConfiguration(
        configuration_id="codex-prototype",
        agent_name="codex",
        agent_version="0.153.0",
        model_provider="openai",
        model_name="model-must-be-confirmed",
        authentication_type="chatgpt_auth_json",
        credential_configuration_id="owner-codex-login",
        critical_config={"reasoning_effort": "medium"},
    )


def _task() -> EvaluationTask:
    return EvaluationTask(
        dataset_id="SWE-Gym/SWE-Gym-Lite",
        dataset_revision="a" * 40,
        split="train",
        instance_id="python__mypy-15413",
        repo="python/mypy",
        base_commit="b" * 40,
        problem_statement="Public issue",
        environment_image="example.invalid/image@sha256:" + "c" * 64,
        raw_record_sha256="d" * 64,
    )


def _request() -> ExecutionJobRequest:
    return ExecutionJobRequest(
        job_id="m0-test-job",
        runs=(ExecutionRunRequest("m0-test-run", _task(), _agent()),),
        limits=RunLimits(900, 1, 4096, 8192),
        backend_revision=HARBOR_REVISION,
        artifact_contract_version=ARTIFACT_CONTRACT_VERSION,
    )


def test_job_plan_freezes_harbor_safety_settings(tmp_path: Path) -> None:
    task_dir = tmp_path / "task"
    task_dir.mkdir()

    plan = build_job_plan(
        _request(),
        jobs_dir=tmp_path / "jobs",
        task_dirs={_task().instance_id: task_dir},
    )

    assert plan.run_ids == ("m0-test-run",)
    assert plan.config["n_attempts"] == 1
    assert plan.config["n_concurrent_trials"] == 1
    assert plan.config["retry"]["max_retries"] == 0
    assert plan.config["verifier"] == {"disable": True}
    assert plan.config["environment"]["delete"] is True
    assert plan.config["agents"][0]["kwargs"] == {
        "version": "0.153.0",
        "reasoning_effort": "medium",
        "web_search": "disabled",
    }


def test_job_plan_contains_no_credential_identity_or_secret_path(
    tmp_path: Path,
) -> None:
    task_dir = tmp_path / "task"
    task_dir.mkdir()

    plan = build_job_plan(
        _request(),
        jobs_dir=tmp_path / "jobs",
        task_dirs={_task().instance_id: task_dir},
    )
    serialized = json.dumps(plan.config, sort_keys=True)

    assert "owner-codex-login" not in serialized
    assert "auth.json" not in serialized
    assert "CODEX_AUTH_JSON_PATH" not in serialized


def test_unknown_backend_revision_is_rejected(tmp_path: Path) -> None:
    request = _request()
    invalid = ExecutionJobRequest(
        job_id=request.job_id,
        runs=request.runs,
        limits=request.limits,
        backend_revision="0" * 40,
        artifact_contract_version=request.artifact_contract_version,
    )

    with pytest.raises(ValueError, match="revision is not registered"):
        build_job_plan(invalid, jobs_dir=tmp_path, task_dirs={})


def test_agent_fingerprint_is_stable_and_deeply_immutable() -> None:
    nested = {"reasoning_effort": "medium", "options": {"flags": ["a", "b"]}}
    agent = AgentConfiguration(
        configuration_id="one",
        agent_name="codex",
        agent_version="0.153.0",
        model_provider="openai",
        model_name="fixed-model",
        authentication_type="chatgpt_auth_json",
        credential_configuration_id="logical-credential",
        critical_config=nested,
    )
    before = agent.fingerprint
    nested["options"]["flags"].append("changed")  # type: ignore[index,union-attr]

    assert agent.fingerprint == before
    with pytest.raises(TypeError):
        agent.critical_config["new"] = "value"  # type: ignore[index]
