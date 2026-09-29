"""Guarded Codex specialization for the isolated provider proxy route."""

from __future__ import annotations

import importlib
import tomllib
from pathlib import Path
from typing import Any, cast

from eval_platform.adapters.execution.codex.agent import guarded_codex_class
from eval_platform.adapters.execution.codex.install import VERSION
from eval_platform.adapters.execution.codex.policy import HOME_PATH, permission_config
from eval_platform.adapters.execution.codex.provider_config import (
    TOKEN_SOURCE,
    render_provider_config,
)
from eval_platform.adapters.execution.codex.uploads import CodexUploads
from eval_platform.domain.agent import INTERNAL_TEST_MODEL, INTERNAL_TEST_PROVIDER

PROXY_BASE_URL = "http://proxy:8080"
FIXED_PROVIDER_CODEX = {
    "name": "codex",
    "model_name": f"{INTERNAL_TEST_PROVIDER}/{INTERNAL_TEST_MODEL}",
    "n_concurrent": 1,
    "kwargs": {
        "version": VERSION,
        "reasoning_effort": "medium",
        "web_search": "disabled",
    },
}


def provider_effective_config(workspace: str) -> dict[str, Any]:
    """Merge the credential-free provider entry into the fixed permission policy."""
    rendered = render_provider_config(
        provider=INTERNAL_TEST_PROVIDER,
        base_url=PROXY_BASE_URL,
        token_source=TOKEN_SOURCE,
    )
    provider = tomllib.loads(rendered.text)
    overlap = set(provider).intersection(permission_config(workspace))
    if overlap:
        raise ValueError("PROVIDER_CONFIG_INVALID")
    return {**permission_config(workspace), **provider}


def guarded_provider_codex_class(*, auth_path: Path, bundle_root: Path) -> type[Any]:
    """Bind fixed offline Codex to the proxy config and private token transfer."""
    base = guarded_codex_class(auth_path=auth_path, bundle_root=bundle_root)
    guarded = type(
        "GuardedProviderCodex",
        (_ProviderCodexMixin, base),
        {"__module__": __name__},
    )
    return cast(type[Any], guarded)


class _ProviderCodexMixin:
    _guard_workspace: str

    def _build_effective_config(
        self, openai_base_url: str | None = None
    ) -> dict[str, Any]:
        if openai_base_url is not None:
            raise ValueError("PROVIDER_CONFIG_INVALID")
        return provider_effective_config(self._guard_workspace)

    async def _upload_effective_config(
        self, environment: Any, config: dict[str, Any], remote_path: str
    ) -> None:
        if (
            remote_path != f"{HOME_PATH}/config.toml"
            or config != provider_effective_config(self._guard_workspace)
        ):
            raise ValueError("PROVIDER_CONFIG_INVALID")
        uploads = CodexUploads(environment)
        token = await uploads.fetch_proxy_run_token()
        await uploads.upload_run_token(token)
        serializer = importlib.import_module("toml")
        document = serializer.dumps(config).encode("utf-8")
        await uploads.upload_config_text(document)
