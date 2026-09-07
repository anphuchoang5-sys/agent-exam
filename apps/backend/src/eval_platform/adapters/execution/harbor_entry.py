"""Fixed Harbor CLI bootstrap; real Agent execution remains gated in M0."""

from __future__ import annotations

import argparse
import importlib
import json
import os
import sys
import tomllib
from pathlib import Path
from typing import Any

from eval_platform.adapters.execution.harbor.config_mapper import HARBOR_REVISION
from eval_platform.adapters.execution.network import (
    compose_profile,
    export_sidecar,
    validate_hosts,
)
from eval_platform.application.ports.execution import RunLimits


def harbor_command(executable: Path, config: Path) -> list[str]:
    interpreter = executable.with_name(
        "python.exe" if executable.suffix == ".exe" else "python"
    )
    if not interpreter.is_file():
        raise FileNotFoundError("The configured Harbor Python is unavailable")
    return [
        str(interpreter.resolve()),
        str(Path(__file__).resolve()),
        "--config",
        str(config.resolve()),
        "--harbor-root",
        str(executable.resolve().parents[2]),
    ]


def harbor_environment() -> dict[str, str]:
    permitted = set(
        (
            "PATH PATHEXT SYSTEMROOT WINDIR COMSPEC TEMP TMP LOCALAPPDATA APPDATA "
            "USERPROFILE HOMEDRIVE HOMEPATH"
        ).split()
    )
    result = {
        key: value for key, value in os.environ.items() if key.upper() in permitted
    }
    result.update(
        HARBOR_TELEMETRY="disabled",
        PYTHONUTF8="1",
        PYTHONIOENCODING="utf-8",
        PYTHONDONTWRITEBYTECODE="1",
        PYTHONSAFEPATH="1",
        PYTHONPATH=str(Path(__file__).resolve().parents[3]),
    )
    return result


def validate_no_model(config: dict[str, Any]) -> None:
    agents = config.get("agents")
    if (
        not isinstance(agents, list)
        or not agents
        or any(
            not isinstance(agent, dict)
            or agent.get("name") != "nop"
            or set(agent) - {"name", "n_concurrent"}
            for agent in agents
        )
    ):
        raise ValueError("REAL_CODEX_NOT_READY")


def validate_network_config(config: dict[str, Any]) -> None:
    environment = config["environment"]
    hosts = tuple(environment.get("extra_allowed_hosts", []))
    if hosts != validate_hosts(hosts) or any(
        environment.get(key)
        for key in ("kwargs", "extra_docker_compose", "import_path", "env", "mounts")
    ):
        raise ValueError("HARBOR_NETWORK_CONFIG_INVALID")
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


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--harbor-root", type=Path, required=True)
    args = parser.parse_args()
    config = json.loads(args.config.read_text(encoding="utf-8"))
    validate_no_model(config)
    validate_network_config(config)
    context = args.config.parent / "sidecar-source"
    export_sidecar(args.harbor_root, context, HARBOR_REVISION)
    harbor = importlib.import_module("harbor")
    if (
        harbor.__file__ is None
        or Path(harbor.__file__).resolve().parent
        != (args.harbor_root / "src/harbor").resolve()
    ):
        raise ValueError("HARBOR_IMPORT_SOURCE_MISMATCH")
    docker = importlib.import_module("harbor.environments.docker.docker")
    docker.DockerEnvironment._EGRESS_CONTROL_SIDECAR_CONTEXT_PATH = context
    cli = importlib.import_module("harbor.cli.main")
    sys.argv = ["harbor", "run", "--config", str(args.config), "--yes"]
    cli.app()


if __name__ == "__main__":
    main()
