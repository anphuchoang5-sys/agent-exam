"""S10 runtime composition stays fixed before the Harbor subprocess starts."""

from __future__ import annotations

import json

import pytest

from eval_platform.adapters.execution.codex.provider import provider_effective_config
from eval_platform.adapters.execution.harbor_entry import validate_agent_mode
from eval_platform.adapters.execution.provider_access.net.runtime import (
    ProviderRuntimePlan,
    load_provider_runtime,
)
from eval_platform.application.ports.execution import (
    ExecutionJobRequest,
    ExecutionRunRequest,
    RunLimits,
)
from eval_platform.delivery.catalog_presets import (
    AGENT_PRESETS,
    INTERNAL_TEST_AGENT_PRESETS,
)
from eval_platform.domain.task import EvaluationTask

IMAGE = "sha256:" + "c" * 64


def _request(*, internal: bool) -> ExecutionJobRequest:
    presets = INTERNAL_TEST_AGENT_PRESETS if internal else AGENT_PRESETS
    agent = next(iter(presets.values()))[1]
    task = EvaluationTask(
        "dataset",
        "revision",
        "train",
        "python__mypy-15413",
        "python/mypy",
        "a" * 40,
        "public issue",
        "image@sha256:" + "b" * 64,
        "c" * 64,
    )
    return ExecutionJobRequest(
        "job-one",
        (ExecutionRunRequest("run-one", task, agent),),
        RunLimits(300, 1, 2048, 4096),
        "6af8d6e31eced13b93849cdf80feeadf24603d15",
        "agentexam.m0.v1",
    )


def test_runtime_plan_writes_only_fixed_non_secret_inputs(tmp_path):
    plan = ProviderRuntimePlan.create(_request(internal=True), tmp_path, IMAGE)
    config = {"environment": {}}
    plan.apply(config)

    assert plan.scope.startswith("t05-s10-")
    assert config["environment"]["extra_docker_compose"] == [
        str(plan.compose_path.resolve())
    ]
    overlay = json.loads(plan.compose_path.read_text())
    assert overlay["services"]["proxy"]["image"] == IMAGE
    assert overlay["services"]["main"]["networks"] == ["internal"]
    assert plan.auth_placeholder.read_text() == "{}\n"
    assert "token" not in plan.manifest_path.read_text().lower()

    loaded = load_provider_runtime(tmp_path / "harbor-config.json")
    assert loaded is not None
    assert (loaded.scope, loaded.image_id, loaded.compose_path) == (
        plan.scope,
        IMAGE,
        plan.compose_path.resolve(),
    )
    plan.cleanup_private_inputs()
    assert not plan.auth_placeholder.exists()


def test_runtime_plan_rejects_chatgpt_or_manifest_tampering(tmp_path):
    with pytest.raises(ValueError, match="PROVIDER_TOPOLOGY_INVALID"):
        ProviderRuntimePlan.create(_request(internal=False), tmp_path, IMAGE)
    plan = ProviderRuntimePlan.create(_request(internal=True), tmp_path, IMAGE)
    plan.manifest_path.write_text('{"version": 1}', encoding="utf-8")
    with pytest.raises(ValueError, match="HARBOR_NETWORK_CONFIG_INVALID"):
        load_provider_runtime(tmp_path / "harbor-config.json")


def test_provider_effective_config_uses_file_auth_without_a_credential_value():
    document = provider_effective_config("/testbed")
    provider = document["model_providers"]["internal_test_fake"]
    assert document["model_provider"] == "internal_test_fake"
    assert provider["base_url"] == "http://proxy:8080"
    assert provider["auth"] == {
        "command": "/bin/cat",
        "args": ["/tmp/codex-secrets/run-token"],
        "timeout_ms": 5000,
        "refresh_interval_ms": 0,
    }
    assert "FAKE-T05" not in json.dumps(document)


def test_harbor_entry_accepts_provider_agent_only_with_runtime_manifest():
    config = {
        "agents": [
            {
                "name": "codex",
                "model_name": "internal_test_fake/deepseek-flash",
                "n_concurrent": 1,
                "kwargs": {
                    "version": "0.153.0",
                    "reasoning_effort": "medium",
                    "web_search": "disabled",
                },
            }
        ]
    }
    assert (
        validate_agent_mode(config, runtime_bound=True, provider_bound=True)
        == "provider_codex"
    )
    with pytest.raises(ValueError, match="REAL_CODEX_CONFIG_INVALID"):
        validate_agent_mode(config, runtime_bound=True, provider_bound=False)
