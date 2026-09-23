import asyncio
from pathlib import Path
from typing import Any

import pytest

from eval_platform.adapters.execution.harbor.lifecycle.cleanup import (
    compose_cleanup_failure_path,
    install_compose_cleanup_timeout,
)


class FakeDockerEnvironment:
    def __init__(self) -> None:
        self.calls: list[tuple[list[str], int | None]] = []

    async def _run_docker_compose_command(
        self,
        command: list[str],
        check: bool = True,
        timeout_sec: int | None = None,
        stdin_data: bytes | None = None,
        on_output: Any = None,
    ) -> tuple[bool, bytes | None, Any]:
        del check
        self.calls.append((command, timeout_sec))
        return True, stdin_data, on_output


class DefaultTimeoutDockerEnvironment(FakeDockerEnvironment):
    async def _run_docker_compose_command(self, *args: Any, **kwargs: Any) -> Any:
        return await super()._run_docker_compose_command(*args, **kwargs)


class IdempotentDockerEnvironment(FakeDockerEnvironment):
    async def _run_docker_compose_command(self, *args: Any, **kwargs: Any) -> Any:
        return await super()._run_docker_compose_command(*args, **kwargs)


def test_compose_cleanup_gets_default_timeout_without_changing_other_calls(
    tmp_path: Path,
) -> None:
    install_compose_cleanup_timeout(
        DefaultTimeoutDockerEnvironment, tmp_path, timeout_sec=7
    )
    environment = DefaultTimeoutDockerEnvironment()

    assert asyncio.run(environment._run_docker_compose_command(["stop"]))[0]
    assert asyncio.run(environment._run_docker_compose_command(["down", "--volumes"]))[
        0
    ]
    assert asyncio.run(environment._run_docker_compose_command(["up"]))[0]
    assert asyncio.run(
        environment._run_docker_compose_command(["down"], timeout_sec=3)
    )[0]

    assert environment.calls == [
        (["stop"], 7),
        (["down", "--volumes"], 7),
        (["up"], None),
        (["down"], 3),
    ]


def test_compose_cleanup_timeout_installation_is_idempotent(tmp_path: Path) -> None:
    install_compose_cleanup_timeout(
        IdempotentDockerEnvironment, tmp_path, timeout_sec=7
    )
    install_compose_cleanup_timeout(
        IdempotentDockerEnvironment, tmp_path, timeout_sec=11
    )
    environment = IdempotentDockerEnvironment()

    asyncio.run(environment._run_docker_compose_command(["down"]))

    assert environment.calls == [(["down"], 7)]


def test_compose_cleanup_timeout_must_be_positive() -> None:
    class UnpatchedDockerEnvironment(FakeDockerEnvironment):
        pass

    with pytest.raises(ValueError, match="must be positive"):
        install_compose_cleanup_timeout(
            UnpatchedDockerEnvironment, Path("unused"), timeout_sec=0
        )


def test_compose_cleanup_failure_leaves_outer_retry_marker(tmp_path: Path) -> None:
    class FailingDockerEnvironment(FakeDockerEnvironment):
        async def _run_docker_compose_command(self, *args: Any, **kwargs: Any) -> Any:
            raise RuntimeError("compose cleanup failed")

    install_compose_cleanup_timeout(FailingDockerEnvironment, tmp_path, timeout_sec=7)

    with pytest.raises(RuntimeError, match="cleanup failed"):
        asyncio.run(FailingDockerEnvironment()._run_docker_compose_command(["down"]))

    assert compose_cleanup_failure_path(tmp_path).is_file()
