"""Narrow fixed-Harbor Codex compatibility and runtime binding."""

from __future__ import annotations

import importlib
import re
from pathlib import Path
from typing import Any

from eval_platform.adapters.execution.codex.install import (
    INSTALL_COMMAND,
    INSTALL_PATH,
    INSTALL_ROOT,
    PREPARE_INSTALL_COMMAND,
    VERSION,
    validate_codex_bundle,
)
from eval_platform.adapters.execution.codex.policy import (
    CLEANUP_COMMAND,
    HOME_PATH,
    SECRETS_PATH,
    SETUP_COMMANDS,
    guarded_command,
    is_codex_run,
    permission_config,
    prepare_workspace_command,
)
from eval_platform.adapters.execution.codex.uploads import (
    CodexUploads,
    validate_auth_file,
)


def guarded_codex_class(
    *, auth_path: Path | None = None, bundle_root: Path | None = None
) -> type[Any]:
    """Load upstream types only inside the fixed Harbor interpreter."""
    if (auth_path is None) != (bundle_root is None):
        raise ValueError("CODEX_RUNTIME_BINDING_INCOMPLETE")
    bound_auth = validate_auth_file(auth_path) if auth_path is not None else None
    bound_bundle = (
        validate_codex_bundle(bundle_root) if bundle_root is not None else None
    )
    base = importlib.import_module("harbor.agents.installed.codex").Codex

    class GuardedCodex(base):  # type: ignore[misc, valid-type]  # Runtime-only upstream.
        def __init__(self, *, workspace: str = "/testbed", **kwargs: Any) -> None:
            # The fixed AgentFactory always supplies an empty extra_env mapping.
            if kwargs.pop("extra_env", {}) != {}:
                raise ValueError("CODEX_GUARD_CONFIG_INVALID")
            if kwargs.pop("web_search", "disabled") != "disabled":
                raise ValueError("CODEX_GUARD_CONFIG_INVALID")
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
            self._guard_auth = bound_auth
            self._guard_bundle = bound_bundle
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
            if self._guard_auth is None:
                raise RuntimeError("CODEX_CREDENTIAL_BINDING_NOT_READY")
            return self._guard_auth

        async def install(self, environment: Any) -> None:
            if self._guard_bundle is None:
                raise RuntimeError("CODEX_OFFLINE_INSTALL_NOT_READY")
            await super().exec_as_root(environment, command=PREPARE_INSTALL_COMMAND)
            await environment.upload_dir(self._guard_bundle, INSTALL_ROOT)
            await super().exec_as_root(environment, command=INSTALL_COMMAND)
            result = await super().exec_as_agent(
                environment,
                command=self._INSTALL_VERSION_COMMAND,
                env={"PATH": INSTALL_PATH},
            )
            version_lines = [
                line.strip()
                for line in (result.stdout or "").splitlines()
                if line.strip()
            ]
            if not version_lines or version_lines[-1] != f"codex-cli {VERSION}":
                raise RuntimeError("CODEX_OFFLINE_INSTALL_FAILED")

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
            if self._guard_running:
                if is_codex_run(command):
                    command = guarded_command(
                        command,
                        self.model_name.split("/")[-1],
                        self._resolved_flags["reasoning_effort"],
                    )
                    self._guard_launches += 1
                    kwargs["cwd"] = self._guard_workspace
                elif command not in SETUP_COMMANDS:
                    raise ValueError("CODEX_UPSTREAM_COMMAND_MISMATCH")
                env = kwargs.pop("env", None) or {}
                if (
                    set(env) - {"CODEX_HOME"}
                    or env.get("CODEX_HOME", HOME_PATH) != HOME_PATH
                ):
                    raise ValueError("CODEX_UPSTREAM_COMMAND_MISMATCH")
                kwargs["env"] = {**env, "PATH": INSTALL_PATH}
            return await super().exec_as_agent(environment, command=command, **kwargs)

        async def exec_as_root(
            self, environment: Any, command: str, **kwargs: Any
        ) -> Any:
            if self._guard_running:
                owner = str(environment.default_user)
                auth_target = f"{SECRETS_PATH}/auth.json"
                commands = {
                    f"chown {owner} {auth_target}": auth_target,
                    f"chown {owner} {HOME_PATH}/config.toml && "
                    f"chmod 600 {HOME_PATH}/config.toml": f"{HOME_PATH}/config.toml",
                }
                target = commands.get(command)
                if target is None:
                    raise ValueError("CODEX_UPSTREAM_COMMAND_MISMATCH")
                # Transfer already created a 0600 file as this exact user.
                return await super().exec_as_agent(
                    environment,
                    command=f'test "$(stat -c %u:%g:%a {target})" = {owner}:600',
                )
            return await super().exec_as_root(environment, command=command, **kwargs)

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
                await super().run(instruction, CodexUploads(environment), context)
                if self._guard_launches != 1:
                    raise ValueError("CODEX_UPSTREAM_COMMAND_MISMATCH")
            finally:
                self._guard_running = False
                # Also cover setup/upload failures outside upstream run's try block.
                await super().exec_as_agent(environment, command=CLEANUP_COMMAND)

    return GuardedCodex
