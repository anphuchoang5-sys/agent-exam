"""Harbor compatibility under test; real credential binding intentionally closed."""

from __future__ import annotations

import importlib
import re
from pathlib import Path
from typing import Any

from eval_platform.adapters.execution.codex_install import VERSION
from eval_platform.adapters.execution.codex_policy import (
    CLEANUP_COMMAND,
    HOME_PATH,
    SECRETS_PATH,
    SETUP_COMMANDS,
    guarded_command,
    is_codex_run,
    permission_config,
    prepare_workspace_command,
)


def guarded_codex_class() -> type[Any]:
    """Load upstream types only inside the fixed Harbor interpreter."""
    base = importlib.import_module("harbor.agents.installed.codex").Codex

    class GuardedCodex(base):  # type: ignore[misc, valid-type]  # Runtime-only upstream.
        def __init__(self, *, workspace: str = "/testbed", **kwargs: Any) -> None:
            if (
                set(kwargs)
                - {"logs_dir", "model_name", "logger", "version", "reasoning_effort"}
                or kwargs.get("version") != VERSION
                or kwargs.get("reasoning_effort")
                not in {"low", "medium", "high", "xhigh"}
            ):
                raise ValueError("CODEX_GUARD_CONFIG_INVALID")
            self._guard_config = permission_config(workspace)
            self._guard_workspace = workspace
            self._guard_running = False
            self._guard_launches = 0
            super().__init__(config=self._guard_config, web_search="disabled", **kwargs)
            if (
                str(self._REMOTE_CODEX_HOME) != HOME_PATH
                or str(self._REMOTE_CODEX_SECRETS_DIR) != SECRETS_PATH
                or self._resolved_flags.get("reasoning_effort")
                not in {"low", "medium", "high", "xhigh"}
            ):
                raise ValueError("CODEX_GUARD_CONFIG_INVALID")

        def _env_sources(self) -> tuple[dict[str, str], ...]:
            # No ambient host auth, API key, base URL, or force-auth fallback.
            return ({},)

        def _resolve_auth_json_path(self) -> Path:
            raise RuntimeError("CODEX_CREDENTIAL_BINDING_NOT_READY")

        def _build_effective_config(
            self, openai_base_url: str | None = None
        ) -> dict[str, Any]:
            if (
                openai_base_url
                or self.mcp_servers
                or self._base_config != self._guard_config
            ):
                raise ValueError("CODEX_GUARD_CONFIG_INVALID")
            return permission_config(self._guard_workspace)

        async def exec_as_agent(
            self, environment: Any, command: str, **kwargs: Any
        ) -> Any:
            if self._guard_running and is_codex_run(command):
                command = guarded_command(
                    command,
                    self.model_name.split("/")[-1],
                    self._resolved_flags["reasoning_effort"],
                )
                self._guard_launches += 1
                kwargs["cwd"] = self._guard_workspace
            elif self._guard_running and command not in SETUP_COMMANDS:
                raise ValueError("CODEX_UPSTREAM_COMMAND_MISMATCH")
            return await super().exec_as_agent(environment, command=command, **kwargs)

        async def run(self, instruction: str, environment: Any, context: Any) -> None:
            # Fail before touching a container unless the staged auth seam is supplied.
            self._resolve_auth_json_path()
            self._build_effective_config()
            if not re.fullmatch(
                r"[1-9][0-9]*(?::[0-9]+)?", str(environment.default_user)
            ):
                raise ValueError("CODEX_GUARD_NON_ROOT_REQUIRED")
            self._guard_running, self._guard_launches = True, 0
            try:
                await super().exec_as_agent(
                    environment,
                    command=prepare_workspace_command(self._guard_workspace),
                )
                await super().run(instruction, environment, context)
                if self._guard_launches != 1:
                    raise ValueError("CODEX_UPSTREAM_COMMAND_MISMATCH")
            finally:
                self._guard_running = False
                # Also cover setup/upload failures outside upstream run's try block.
                await super().exec_as_agent(environment, command=CLEANUP_COMMAND)

    return GuardedCodex
