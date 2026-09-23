"""Private runtime file transfer; does not resolve host credential configuration."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from eval_platform.adapters.execution.codex.provider_config import TOKEN_SOURCE


def validate_auth_file(source: Path | str) -> Path:
    """Validate metadata without parsing or exposing authentication contents."""
    try:
        path = Path(source)
        if path.is_symlink() or not path.is_file():
            raise ValueError
        size = path.stat().st_size
        if size < 1 or size > 65536:
            raise ValueError
        return path.resolve(strict=True)
    except (OSError, ValueError):
        raise ValueError("CODEX_AUTH_FILE_INVALID") from None


class CodexUploads:
    """Narrow runtime transfer proxy; never puts file contents in argv or logs."""

    TARGETS = frozenset({"/tmp/codex-secrets/auth.json", "/tmp/codex-home/config.toml"})

    def __init__(self, environment: Any) -> None:
        self._environment = environment
        if not re.fullmatch(r"[1-9][0-9]*:[0-9]+", str(environment.default_user)):
            raise ValueError("CODEX_UPLOAD_USER_INVALID")

    def __getattr__(self, name: str) -> Any:
        return getattr(self._environment, name)

    async def upload_file(self, source: Path | str, target: str) -> None:
        if target not in self.TARGETS:
            raise ValueError("CODEX_UPLOAD_TARGET_INVALID")
        try:
            path = validate_auth_file(source)
            with path.open("rb") as stream:
                content = stream.read(65537)
            # Exclusive creation in the private directories prepared by upstream.
            result = await self._environment._run_docker_compose_command(
                [
                    "exec",
                    "-T",
                    "-u",
                    str(self.default_user),
                    "main",
                    "sh",
                    "-c",
                    f"set -C; umask 077; cat > {target}",
                ],
                check=False,
                timeout_sec=30,
                stdin_data=content,
            )
            if result.return_code != 0 or result.stdout or result.stderr:
                raise ValueError("CODEX_UPLOAD_FAILED")
        except Exception:
            # Do not serialize host source paths or subprocess diagnostics.
            raise RuntimeError("CODEX_PRIVATE_UPLOAD_FAILED") from None

    async def upload_run_token(self, token: bytes) -> None:
        """Transfer one short-lived token by stdin, never by host file or argv."""
        if not isinstance(token, bytes) or not re.fullmatch(
            rb"[A-Za-z0-9_-]{16,256}", token
        ):
            raise ValueError("CODEX_RUN_TOKEN_INVALID")
        try:
            result = await self._environment._run_docker_compose_command(
                [
                    "exec",
                    "-T",
                    "-u",
                    str(self.default_user),
                    "main",
                    "sh",
                    "-c",
                    f"set -C; umask 077; cat > {TOKEN_SOURCE}",
                ],
                check=False,
                timeout_sec=30,
                stdin_data=token,
            )
            if result.return_code != 0 or result.stdout or result.stderr:
                raise ValueError("CODEX_RUN_TOKEN_UPLOAD_FAILED")
        except Exception:
            raise RuntimeError("CODEX_PRIVATE_UPLOAD_FAILED") from None

    async def fetch_proxy_run_token(self) -> bytes:
        """Read the proxy's tmpfs token without placing it in argv, env or a file."""
        try:
            result = await self._environment._run_docker_compose_command(
                ["exec", "-T", "proxy", "cat", "/tmp/run-token"],
                check=False,
                timeout_sec=30,
            )
            stdout = result.stdout
            token = stdout.encode("ascii") if isinstance(stdout, str) else stdout
            if (
                result.return_code != 0
                or result.stderr not in (None, "", b"")
                or not isinstance(token, bytes)
                or not re.fullmatch(rb"[A-Za-z0-9_-]{16,256}", token)
            ):
                raise ValueError
            return token
        except Exception:
            raise RuntimeError("PROVIDER_TOKEN_UNAVAILABLE") from None

    async def upload_config_text(self, document: bytes) -> None:
        """Put the rendered, credential-free config in the existing upload target."""
        if not isinstance(document, bytes) or not 0 < len(document) <= 65536:
            raise ValueError("CODEX_CONFIG_UPLOAD_INVALID")
        target = "/tmp/codex-home/config.toml"
        try:
            result = await self._environment._run_docker_compose_command(
                [
                    "exec",
                    "-T",
                    "-u",
                    str(self.default_user),
                    "main",
                    "sh",
                    "-c",
                    f"set -C; umask 077; cat > {target}",
                ],
                check=False,
                timeout_sec=30,
                stdin_data=document,
            )
            if result.return_code != 0 or result.stdout or result.stderr:
                raise ValueError("CODEX_CONFIG_UPLOAD_FAILED")
        except Exception:
            raise RuntimeError("CODEX_PRIVATE_UPLOAD_FAILED") from None
