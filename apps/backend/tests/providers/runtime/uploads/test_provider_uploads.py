"""Provider-specific private uploads stay off argv, env, and host files."""

from __future__ import annotations

import asyncio
import json
from types import SimpleNamespace

import pytest

from eval_platform.adapters.execution.codex.uploads import CodexUploads


class TransferEnvironment:
    default_user = "65534:65534"

    def __init__(self, result=None):
        self.calls = []
        self.result = result or SimpleNamespace(return_code=0, stdout=None, stderr=None)

    async def _run_docker_compose_command(self, args, **kwargs):
        self.calls.append((args, kwargs))
        return self.result


def test_short_lived_token_uses_stdin_without_host_file_or_command_value():
    environment = TransferEnvironment()
    token = b"SYNTHETIC-RUN-TOKEN-NOT-REAL"
    asyncio.run(CodexUploads(environment).upload_run_token(token))
    ((args, options),) = environment.calls
    assert args[-1] == ("set -C; umask 077; cat > /tmp/codex-secrets/run-token")
    assert token.decode() not in repr(args)
    assert options["stdin_data"] == token


@pytest.mark.parametrize("token", [b"", b"a" * 257, b"line\nbreak", b"has space"])
def test_short_lived_token_rejects_invalid_bytes_before_io(token):
    environment = TransferEnvironment()
    with pytest.raises(ValueError, match="CODEX_RUN_TOKEN_INVALID"):
        asyncio.run(CodexUploads(environment).upload_run_token(token))
    assert environment.calls == []


def test_rendered_config_uses_existing_private_upload_target():
    environment = TransferEnvironment()
    document = b'model_provider = "internal_test_fake"\n'
    asyncio.run(CodexUploads(environment).upload_config_text(document))
    ((args, options),) = environment.calls
    assert args[-1] == "set -C; umask 077; cat > /tmp/codex-home/config.toml"
    assert options["stdin_data"] == document


def test_config_upload_rejects_empty_or_oversized_text():
    environment = TransferEnvironment()
    for document in (b"", b"a" * 65537):
        with pytest.raises(ValueError, match="CODEX_CONFIG_UPLOAD_INVALID"):
            asyncio.run(CodexUploads(environment).upload_config_text(document))
    assert environment.calls == []


def test_fetches_proxy_token_without_echoing_it_into_compose_arguments():
    token = "A" * 32
    environment = TransferEnvironment(
        SimpleNamespace(return_code=0, stdout=token, stderr="")
    )
    fetched = asyncio.run(CodexUploads(environment).fetch_proxy_run_token())
    assert fetched == token.encode("ascii")
    command, kwargs = environment.calls[0]
    assert command == ["exec", "-T", "proxy", "cat", "/tmp/run-token"]
    assert token not in json.dumps([command, kwargs], default=str)


@pytest.mark.parametrize(
    "result",
    [
        SimpleNamespace(return_code=1, stdout="", stderr="failed"),
        SimpleNamespace(return_code=0, stdout="short", stderr=""),
        SimpleNamespace(return_code=0, stdout="A" * 32, stderr="unexpected"),
    ],
)
def test_missing_or_malformed_proxy_token_fails_closed(result):
    environment = TransferEnvironment(result)
    with pytest.raises(RuntimeError, match="PROVIDER_TOKEN_UNAVAILABLE"):
        asyncio.run(CodexUploads(environment).fetch_proxy_run_token())
