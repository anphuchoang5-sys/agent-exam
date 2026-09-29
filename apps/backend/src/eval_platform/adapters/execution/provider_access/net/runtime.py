"""Create and reload the one owner-approved provider runtime description."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from eval_platform.adapters.execution.provider_access.net.topology import (
    compose_overlay,
)
from eval_platform.application.ports.execution import ExecutionJobRequest
from eval_platform.domain.agent import (
    INTERNAL_TEST_CREDENTIAL_ID,
    INTERNAL_TEST_IDENTITY,
)

_VERSION = 1
_MANIFEST = "provider-runtime.json"
_COMPOSE = "provider-compose.json"
_AUTH_PLACEHOLDER = ".provider-auth-placeholder.json"


@dataclass(frozen=True, slots=True)
class LoadedProviderRuntime:
    scope: str
    image_id: str
    compose_path: Path


@dataclass(frozen=True, slots=True)
class ProviderRuntimePlan:
    """Run-local files passed through the existing Harbor adapter boundary."""

    scope: str
    image_id: str
    compose_path: Path
    manifest_path: Path
    auth_placeholder: Path

    @classmethod
    def create(
        cls, request: ExecutionJobRequest, run_root: Path, image_id: str
    ) -> ProviderRuntimePlan:
        if len(request.runs) != 1:
            raise ValueError("PROVIDER_TOPOLOGY_INVALID")
        agent = request.runs[0].agent
        if (
            (agent.model_provider, agent.authentication_type) != INTERNAL_TEST_IDENTITY
            or agent.credential_configuration_id != INTERNAL_TEST_CREDENTIAL_ID
        ):
            raise ValueError("PROVIDER_TOPOLOGY_INVALID")
        identity = f"{request.job_id}:{request.runs[0].run_id}".encode()
        scope = "t05-s10-" + hashlib.sha256(identity).hexdigest()[:20]
        compose = run_root / _COMPOSE
        manifest = run_root / _MANIFEST
        placeholder = run_root / _AUTH_PLACEHOLDER
        overlay = compose_overlay(
            scope=scope, proxy_image=image_id, upstream_image=image_id
        )
        _write_json_exclusive(compose, overlay)
        _write_json_exclusive(
            manifest,
            {
                "version": _VERSION,
                "scope": scope,
                "image_id": image_id,
                "compose_path": str(compose.resolve()),
            },
        )
        with placeholder.open("x", encoding="utf-8", newline="\n") as stream:
            stream.write("{}\n")
        return cls(scope, image_id, compose, manifest, placeholder)

    def apply(self, config: dict[str, Any]) -> None:
        environment = config.get("environment")
        if not isinstance(environment, dict) or environment.get("extra_docker_compose"):
            raise ValueError("HARBOR_NETWORK_CONFIG_INVALID")
        environment["extra_docker_compose"] = [str(self.compose_path.resolve())]

    def cleanup_private_inputs(self) -> None:
        self.auth_placeholder.unlink(missing_ok=True)


def load_provider_runtime(config_path: Path) -> LoadedProviderRuntime | None:
    path = config_path.resolve().parent / _MANIFEST
    if not path.exists():
        return None
    try:
        if path.is_symlink() or path.stat().st_size > 4096:
            raise ValueError
        value = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(value, dict) or set(value) != {
            "version",
            "scope",
            "image_id",
            "compose_path",
        }:
            raise ValueError
        if value["version"] != _VERSION:
            raise ValueError
        compose = path.parent / _COMPOSE
        loaded = LoadedProviderRuntime(
            value["scope"], value["image_id"], compose.resolve()
        )
        if value["compose_path"] != str(loaded.compose_path):
            raise ValueError
        compose_overlay(
            scope=loaded.scope,
            proxy_image=loaded.image_id,
            upstream_image=loaded.image_id,
        )
        return loaded
    except (KeyError, OSError, TypeError, UnicodeError, ValueError):
        raise ValueError("HARBOR_NETWORK_CONFIG_INVALID") from None


def _write_json_exclusive(path: Path, value: Any) -> None:
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, indent=2, sort_keys=True)
        stream.write("\n")
