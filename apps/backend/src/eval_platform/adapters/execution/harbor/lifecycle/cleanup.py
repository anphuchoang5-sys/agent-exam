import json
import re
import subprocess
from pathlib import Path
from typing import Any

from eval_platform.domain.jobs.policy import PROCESS_TERMINATION_GRACE_SEC

_DOCKER_TIMEOUT_SEC = 30
_CLEANUP_TIMEOUT_MARKER = "__agentexam_compose_cleanup_timeout__"
COMPOSE_CLEANUP_RETRY_WARNING = "HARBOR_COMPOSE_CLEANUP_RETRIED"
_CLEANUP_FAILURE_MARKER = "harbor-compose-cleanup-failed"
_COMPOSE_RESOURCES = (
    (["container", "ls", "--all"], ["container", "rm", "--force"]),
    (["network", "ls"], ["network", "rm"]),
    (["volume", "ls"], ["volume", "rm", "--force"]),
    (["image", "ls"], ["image", "rm"]),
)


def install_compose_cleanup_timeout(
    docker_environment: type[Any],
    evidence_root: Path,
    *,
    timeout_sec: int = PROCESS_TERMINATION_GRACE_SEC,
) -> None:
    """Bound Harbor's otherwise unbounded Compose stop/down commands."""

    if timeout_sec <= 0:
        raise ValueError("Compose cleanup timeout must be positive")
    cleanup_timeout_sec = timeout_sec
    original = docker_environment._run_docker_compose_command
    if getattr(original, _CLEANUP_TIMEOUT_MARKER, False):
        return

    async def bounded(
        instance: Any,
        command: list[str],
        check: bool = True,
        timeout_sec: int | None = None,
        stdin_data: bytes | None = None,
        on_output: Any = None,
    ) -> Any:
        is_cleanup = command[:1] in (["stop"], ["down"])
        if timeout_sec is None and is_cleanup:
            timeout_sec = cleanup_timeout_sec
        try:
            return await original(
                instance,
                command,
                check=check,
                timeout_sec=timeout_sec,
                stdin_data=stdin_data,
                on_output=on_output,
            )
        except Exception:
            if is_cleanup:
                compose_cleanup_failure_path(evidence_root).touch(
                    mode=0o600, exist_ok=True
                )
            raise

    setattr(bounded, _CLEANUP_TIMEOUT_MARKER, True)
    docker_environment._run_docker_compose_command = bounded


def compose_cleanup_failure_path(evidence_root: Path) -> Path:
    return evidence_root / _CLEANUP_FAILURE_MARKER


def cleanup_timed_out_projects(job_dir: Path) -> tuple[str, ...]:
    configs = sorted(job_dir.glob("*/config.json"))
    if not configs:
        return ("HARBOR_COMPOSE_CLEANUP_UNVERIFIED",)
    failed = False
    for path in configs:
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
            trial_name = value.get("trial_name")
            if not isinstance(trial_name, str) or trial_name != path.parent.name:
                raise ValueError("Untrusted Harbor Trial identity")
            project = re.sub(r"[^a-z0-9_-]", "-", f"{trial_name}__env".lower())
            for list_args, remove_args in _COMPOSE_RESOURCES:
                ids = _docker_resource_ids(list_args, project)
                if ids:
                    removed = subprocess.run(
                        ["docker", *remove_args, *ids],
                        capture_output=True,
                        timeout=_DOCKER_TIMEOUT_SEC,
                        check=False,
                    )
                    failed |= removed.returncode != 0
                failed |= bool(_docker_resource_ids(list_args, project))
        except (OSError, RuntimeError, subprocess.SubprocessError, ValueError):
            failed = True
    return ("HARBOR_COMPOSE_CLEANUP_FAILED",) if failed else ()


def _docker_resource_ids(list_args: list[str], project: str) -> tuple[str, ...]:
    result = subprocess.run(
        [
            "docker",
            *list_args,
            "--filter",
            f"label=com.docker.compose.project={project}",
            "--quiet",
        ],
        capture_output=True,
        text=True,
        timeout=_DOCKER_TIMEOUT_SEC,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError("Docker resource query failed")
    return tuple(dict.fromkeys(result.stdout.split()))
