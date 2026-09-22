"""Frozen identity and profile must select a binding before Harbor is invoked."""

from pathlib import Path
from types import SimpleNamespace

import pytest

from eval_platform.adapters.artifacts.config import MinioConfig
from eval_platform.delivery.catalog_presets import (
    AGENT_PRESETS,
    INTERNAL_TEST_AGENT_PRESETS,
)
from eval_platform.delivery.worker import runtime as runtime_module
from eval_platform.delivery.worker.bindings import (
    CHATGPT_NETWORK_HOSTS,
    RunBoundExecutionBackend,
    select_run_binding,
)
from eval_platform.delivery.worker.runtime import RuntimeWorkerConfig


def _agent(internal: bool = False):
    presets = INTERNAL_TEST_AGENT_PRESETS if internal else AGENT_PRESETS
    return next(iter(presets.values()))[1]


def _request(*agents: object) -> SimpleNamespace:
    return SimpleNamespace(runs=tuple(SimpleNamespace(agent=agent) for agent in agents))


def test_chatgpt_identity_keeps_fixed_hosts_and_auth_requirement() -> None:
    binding = select_run_binding(_agent())
    assert binding.route == "chatgpt"
    assert binding.network_hosts == CHATGPT_NETWORK_HOSTS
    assert binding.needs_codex_archive is True
    assert binding.needs_chatgpt_auth is True


def test_internal_test_identity_selects_proxy_without_chatgpt_auth() -> None:
    binding = select_run_binding(_agent(internal=True))
    assert binding.route == "provider_proxy"
    assert binding.network_hosts == ()
    assert binding.needs_codex_archive is True
    assert binding.needs_chatgpt_auth is False


@pytest.mark.parametrize(
    ("provider", "authentication"),
    [("unknown", "chatgpt_auth_json"), ("openai_chatgpt", "provider_run_token")],
)
def test_unknown_identity_fails_closed(provider: str, authentication: str) -> None:
    damaged = SimpleNamespace(
        model_provider=provider,
        authentication_type=authentication,
        credential_configuration_id="owner-codex",
    )
    with pytest.raises(ValueError, match="WORKER_AGENT_IDENTITY_INVALID"):
        select_run_binding(damaged)


@pytest.mark.parametrize("internal", [False, True])
def test_credential_reference_must_match_identity(internal: bool) -> None:
    original = _agent(internal=internal)
    damaged = SimpleNamespace(
        model_provider=original.model_provider,
        authentication_type=original.authentication_type,
        credential_configuration_id=(
            "owner-codex" if internal else "t05-fake-provider"
        ),
    )
    with pytest.raises(ValueError, match="WORKER_CREDENTIAL_BINDING_INVALID"):
        select_run_binding(damaged)


def test_chatgpt_request_uses_existing_backend_once() -> None:
    observed: list[object] = []
    request = _request(_agent())
    progress = object()

    class Backend:
        def execute(self, passed_request: object, passed_progress: object) -> tuple[()]:
            observed.extend((passed_request, passed_progress))
            return ()

    backend = RunBoundExecutionBackend(lambda: Backend())
    assert backend.execute(request, progress) == ()
    assert observed == [request, progress]


@pytest.mark.parametrize("mixed", [False, True])
def test_proxy_request_never_uses_chatgpt_backend(mixed: bool) -> None:
    calls = 0

    def forbidden_chatgpt_backend():
        nonlocal calls
        calls += 1
        raise AssertionError("ChatGPT credentials must remain untouched")

    agents = (_agent(), _agent(True)) if mixed else (_agent(True),)
    backend = RunBoundExecutionBackend(forbidden_chatgpt_backend)
    with pytest.raises(RuntimeError, match="PROVIDER_RUNTIME_NOT_READY"):
        backend.execute(_request(*agents))
    assert calls == 0


def test_chatgpt_backend_requires_both_private_inputs() -> None:
    project = Path.cwd().resolve()
    config = RuntimeWorkerConfig(
        project,
        project / "runtime" / "acceptance" / "missing-auth",
        project / "task.parquet",
        project / "codex.tgz",
        None,
        "host=127.0.0.1 password=must-not-connect",
        MinioConfig(
            "http://127.0.0.1:9000", "bucket", "access-secret", "object-secret"
        ),
    )
    with pytest.raises(ValueError, match="CODEX_RUNTIME_BINDING_INCOMPLETE"):
        runtime_module._create_chatgpt_backend(config)


def test_chatgpt_backend_keeps_fixed_harbor_inputs(monkeypatch) -> None:
    project = Path.cwd().resolve()
    archive, auth = project / "codex.tgz", project / "auth.json"
    config = RuntimeWorkerConfig(
        project,
        project / "runtime" / "acceptance" / "chatgpt-binding",
        project / "task.parquet",
        archive,
        auth,
        "host=127.0.0.1 password=must-not-connect",
        MinioConfig("http://127.0.0.1:9000", "bucket", "access", "secret"),
    )
    checked: list[Path] = []
    captured: dict[str, object] = {}
    adapter = object()
    monkeypatch.setattr(
        runtime_module, "_verify_codex_archive", lambda path: checked.append(path)
    )
    monkeypatch.setattr(
        runtime_module, "validate_auth_file", lambda path: checked.append(path)
    )

    def make_adapter(*args: object, **kwargs: object) -> object:
        captured.update(args=args, kwargs=kwargs)
        return adapter

    monkeypatch.setattr(runtime_module, "HarborExecutionAdapter", make_adapter)
    assert runtime_module._create_chatgpt_backend(config) is adapter
    assert checked == [archive, auth]
    assert captured["kwargs"] == {
        "network_hosts": ("auth.openai.com", "chatgpt.com"),
        "codex_archive": archive,
        "codex_auth_path": auth,
    }
