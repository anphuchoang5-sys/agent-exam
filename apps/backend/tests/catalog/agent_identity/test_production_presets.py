"""Production Codex presets survive owner registration and fixed Harbor mapping."""

from pathlib import Path
from uuid import UUID

import pytest
from identity.conftest import WRITE_HEADERS

from catalog.conftest import catalog_api, task_bundle
from eval_platform.adapters.execution.harbor.config_mapper import (
    ARTIFACT_CONTRACT_VERSION,
    HARBOR_REVISION,
    build_job_plan,
)
from eval_platform.adapters.execution.harbor_entry import validate_agent_mode
from eval_platform.application.ports.execution import (
    ExecutionJobRequest,
    ExecutionRunRequest,
    RunLimits,
)
from eval_platform.delivery.catalog_presets import AGENT_PRESETS


@pytest.mark.parametrize(
    ("preset_id", "model", "effort"),
    [
        ("codex-0153-terra-medium", "gpt-5.6-terra", "medium"),
        ("codex-0153-luna-low", "gpt-5.6-luna", "low"),
        ("codex-0153-sol-medium", "gpt-5.6-sol", "medium"),
    ],
)
def test_owner_registers_distinct_fixed_runtime(
    tmp_path: Path, preset_id: str, model: str, effort: str
) -> None:
    assert len(AGENT_PRESETS) == 3
    with catalog_api(agent_presets=AGENT_PRESETS) as api:
        assert api.login().status_code == 200
        endpoint = "/api/v1/agent-configurations"
        response = api.client.post(
            endpoint, json={"preset_id": preset_id}, headers=WRITE_HEADERS
        )
        assert response.status_code == 201
        registered = response.json()
        record_id = registered["agent_configuration_id"]
        assert str(UUID(record_id)) == record_id
        assert registered["model"] == model
        assert registered["public_options"] == {"reasoning_effort": effort}
        assert registered["model_provider"] == "openai_chatgpt"
        assert (
            api.client.post(
                endpoint, json={"preset_id": preset_id}, headers=WRITE_HEADERS
            ).json()
            == registered
        )
        page = api.client.get(endpoint, params={"limit": 100, "agent_type": "codex"})
        assert page.status_code == 200
        matches = [
            item
            for item in page.json()["items"]
            if item["agent_configuration_id"] == record_id
        ]
        assert len(matches) == 1
        assert matches[0]["model"] == model
        assert matches[0]["enabled"] is True

    task = task_bundle().public
    configuration = AGENT_PRESETS[preset_id][1]
    request = ExecutionJobRequest(
        job_id="registered-codex",
        runs=(ExecutionRunRequest("registered-run", task, configuration),),
        limits=RunLimits(900, 1, 4096, 8192),
        backend_revision=HARBOR_REVISION,
        artifact_contract_version=ARTIFACT_CONTRACT_VERSION,
    )
    plan = build_job_plan(
        request,
        jobs_dir=tmp_path / "jobs",
        task_dirs={task.instance_id: tmp_path / "task"},
    )
    mapped = plan.config["agents"][0]
    assert mapped["model_name"] == f"openai/{model}"
    assert mapped["kwargs"]["reasoning_effort"] == effort
    assert validate_agent_mode(plan.config, runtime_bound=True) == "codex"


def test_fixed_runtime_rejects_modified_or_repeated_presets() -> None:
    from copy import deepcopy

    agents = [
        {
            "name": "codex",
            "model_name": "openai/gpt-5.6-sol",
            "n_concurrent": 1,
            "kwargs": {
                "version": "0.153.0",
                "reasoning_effort": "medium",
                "web_search": "disabled",
            },
        }
    ]
    assert validate_agent_mode({"agents": agents}, runtime_bound=True) == "codex"
    for changed in (
        [{**agents[0], "model_name": "openai/unknown"}],
        [{**agents[0], "kwargs": {**agents[0]["kwargs"], "reasoning_effort": "high"}}],
        agents * 2,
        [*agents, {"name": "nop", "n_concurrent": 1}],
    ):
        with pytest.raises(ValueError, match="REAL_CODEX_CONFIG_INVALID"):
            validate_agent_mode({"agents": deepcopy(changed)}, runtime_bound=True)


def test_three_fixed_presets_form_one_harbor_matrix(tmp_path: Path) -> None:
    task = task_bundle().public
    runs = tuple(
        ExecutionRunRequest(f"preset-{index}", task, configuration)
        for index, (_, configuration) in enumerate(AGENT_PRESETS.values())
    )
    request = ExecutionJobRequest(
        job_id="three-fixed-presets",
        runs=runs,
        limits=RunLimits(900, 1, 4096, 8192),
        backend_revision=HARBOR_REVISION,
        artifact_contract_version=ARTIFACT_CONTRACT_VERSION,
    )
    plan = build_job_plan(
        request,
        jobs_dir=tmp_path / "jobs",
        task_dirs={task.instance_id: tmp_path / "task"},
    )
    assert len(plan.config["agents"]) == 3
    assert len(plan.bindings) == 3
    assert validate_agent_mode(plan.config, runtime_bound=True) == "codex"
