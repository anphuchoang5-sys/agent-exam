"""The product gate accepts only its internally generated provider overlay."""

import json

import pytest

from eval_platform.adapters.execution.harbor.config_mapper import build_job_plan
from eval_platform.adapters.execution.harbor_entry import validate_network_config
from eval_platform.adapters.execution.provider_access.net import topology
from eval_platform.adapters.tasks.swe_gym import render_harbor_task

pytestmark = pytest.mark.contract


def test_only_exact_internal_provider_overlay_passes_product_gate(pipeline, tmp_path):
    scope = "t05-s10-run-001"
    proxy_image, upstream_image = "sha256:" + "a" * 64, "sha256:" + "b" * 64
    plan = build_job_plan(
        pipeline.request,
        jobs_dir=tmp_path / "jobs",
        task_dirs={
            pipeline.bundle.public.instance_id: render_harbor_task(
                pipeline.bundle.public, tmp_path / "tasks", pipeline.request.limits
            )
        },
    )
    compose = tmp_path / "provider-compose.json"
    overlay = topology.compose_overlay(
        scope=scope, proxy_image=proxy_image, upstream_image=upstream_image
    )
    compose.write_text(json.dumps(overlay))
    plan.config["environment"]["extra_docker_compose"] = [str(compose.resolve())]

    validate_network_config(
        plan.config,
        provider_compose=compose,
        provider_scope=scope,
        proxy_image=proxy_image,
        upstream_image=upstream_image,
    )
