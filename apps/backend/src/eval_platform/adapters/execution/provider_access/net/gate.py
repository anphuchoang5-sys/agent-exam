"""Recheck Harbor's task baseline and the only allowed S10 Compose overlay."""

from __future__ import annotations

import json
import tomllib
from pathlib import Path
from typing import Any

from eval_platform.adapters.execution.network import compose_profile, validate_hosts
from eval_platform.adapters.execution.provider_access.net.topology import (
    validate_compose_file,
)
from eval_platform.application.ports.execution import RunLimits


def validate_network_config(
    config: dict[str, Any],
    *,
    provider_compose: Path | None = None,
    provider_scope: str | None = None,
    proxy_image: str | None = None,
    upstream_image: str | None = None,
) -> None:
    """Leave the existing ChatGPT gate strict; opt in only to one exact overlay."""
    environment = config["environment"]
    hosts = tuple(environment.get("extra_allowed_hosts", []))
    if hosts != validate_hosts(hosts) or any(
        environment.get(key) for key in ("kwargs", "import_path", "env", "mounts")
    ):
        raise ValueError("HARBOR_NETWORK_CONFIG_INVALID")
    overlays = environment.get("extra_docker_compose", [])
    if provider_compose is None:
        if overlays or any(
            item is not None for item in (provider_scope, proxy_image, upstream_image)
        ):
            raise ValueError("HARBOR_NETWORK_CONFIG_INVALID")
    else:
        if (
            provider_scope is None
            or proxy_image is None
            or upstream_image is None
            or hosts
        ):
            raise ValueError("HARBOR_NETWORK_CONFIG_INVALID")
        validate_compose_file(
            provider_compose,
            overlays,
            scope=provider_scope,
            proxy_image=proxy_image,
            upstream_image=upstream_image,
        )
    limits = RunLimits(
        1,
        environment["override_cpus"],
        environment["override_memory_mb"],
        environment["override_storage_mb"],
    )
    for reference in config["tasks"]:
        task = Path(reference["path"])
        document = tomllib.loads((task / "task.toml").read_text(encoding="utf-8"))
        if (
            document["environment"].get("network_mode") != "allowlist"
            or document["environment"].get("allowed_hosts") != []
        ):
            raise ValueError("HARBOR_NETWORK_BASELINE_INVALID")
        for phase in ("agent", "verifier"):
            if {"network_mode", "allowed_hosts"}.intersection(document[phase]):
                raise ValueError("HARBOR_NETWORK_PHASE_OVERRIDE")
        profile = json.loads((task / "environment/docker-compose.yaml").read_text())
        if profile != compose_profile(limits):
            raise ValueError("HARBOR_NETWORK_COMPOSE_INVALID")
