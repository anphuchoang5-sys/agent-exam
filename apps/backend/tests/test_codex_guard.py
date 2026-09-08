from __future__ import annotations

import json
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest

from eval_platform.adapters.execution import harbor_entry as entry_module
from eval_platform.adapters.execution.harbor_entry import (
    harbor_environment,
    validate_agent_mode,
)


def test_fixed_upstream_run_uses_guard_and_cleans_all_method_exit_paths(tmp_path):
    repo = Path(__file__).resolve().parents[3]
    interpreter = repo / "framework/harbor/.venv/Scripts/python.exe"
    if not interpreter.is_file():
        pytest.skip("Fixed local Harbor interpreter is not restored")
    result = subprocess.run(
        [
            str(interpreter),
            str(Path(__file__).with_name("codex_guard_probe.py")),
            str(tmp_path),
        ],
        env=harbor_environment(),
        cwd=repo,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=45,
    )
    assert result.returncode == 0, result.stderr[-4000:]
    evidence = json.loads((tmp_path / "guard-contract.json").read_text())
    assert evidence["credential_binding_closed"]
    assert not evidence["environment_executed_commands"]
    assert not evidence["real_codex_ready"]
    assert len(evidence["cases"]) == 5


def test_guard_refuses_ambient_auth_overrides_root_and_unknown_commands(tmp_path):
    repo = Path(__file__).resolve().parents[3]
    interpreter = repo / "framework/harbor/.venv/Scripts/python.exe"
    if not interpreter.is_file():
        pytest.skip("Fixed local Harbor interpreter is not restored")
    program = """import asyncio, os
from pathlib import Path
from types import SimpleNamespace
from eval_platform.adapters.execution.codex.agent import guarded_codex_class
from eval_platform.adapters.execution.codex.install import VERSION
Guard = guarded_codex_class()
kwargs = dict(logs_dir=Path.cwd(), version=VERSION, reasoning_effort="medium",
              model_name="openai/gpt-5.6-terra")
for field, value in (("config", "must-not-read"), ("extra_env", {"X": "forbidden"}),
                     ("web_search", "live"),
                     ("mcp_servers", []), ("version", "latest"),
                     ("reasoning_effort", None)):
    try:
        Guard(**{**kwargs, field: value})
    except ValueError as error:
        assert str(error) == "CODEX_GUARD_CONFIG_INVALID"
    else:
        raise AssertionError(field)
from harbor.agents.factory import AgentFactory
from harbor.models.trial.config import AgentConfig
AgentFactory.get_agent_class = classmethod(lambda cls, name: Guard)
created = AgentFactory.create_agent_from_config(
    AgentConfig(name="codex", model_name=kwargs["model_name"],
                kwargs={"version": VERSION, "reasoning_effort": "medium",
                        "web_search": "disabled"}),
    logs_dir=Path.cwd())
assert created.extra_env == {}
os.environ["OPENAI_API_KEY"] = "AGENTEXAM-FAKE-AMBIENT"
os.environ["CODEX_FORCE_AUTH_JSON"] = "1"
class FakeGuard(Guard):
    def _resolve_auth_json_path(self):
        return Path("synthetic-never-opened")
agent = FakeGuard(**kwargs)
assert agent._get_env("OPENAI_API_KEY") is None
assert agent._get_env("CODEX_FORCE_AUTH_JSON") is None
async def checks():
    for identity in (None, "root", "root:root", "0:0", "0", 0):
        try:
            await agent.run("never run", SimpleNamespace(default_user=identity), None)
        except ValueError as error:
            assert str(error) == "CODEX_GUARD_NON_ROOT_REQUIRED"
        else:
            raise AssertionError("Root was accepted")
    agent._guard_running = True
    for command in ("codex exec --yolo task", "sh -c 'codex exec task'",
                    "unknown setup"):
        try:
            await agent.exec_as_agent(None, command)
        except ValueError as error:
            assert str(error) == "CODEX_UPSTREAM_COMMAND_MISMATCH"
        else:
            raise AssertionError("Unknown command reached environment")
asyncio.run(checks())
"""
    result = subprocess.run(
        [str(interpreter), "-c", program],
        cwd=tmp_path,
        env=harbor_environment(),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=45,
    )
    assert result.returncode == 0, result.stderr[-4000:]


def test_fixed_codex_requires_an_explicit_private_runtime(tmp_path: Path) -> None:
    fixed = {
        "agents": [
            {
                "name": "codex",
                "model_name": "openai/gpt-5.6-terra",
                "n_concurrent": 1,
                "kwargs": {
                    "version": "0.153.0",
                    "reasoning_effort": "medium",
                    "web_search": "disabled",
                },
            }
        ]
    }
    assert validate_agent_mode(fixed, runtime_bound=True) == "codex"
    with pytest.raises(RuntimeError, match="BINDING_NOT_READY"):
        validate_agent_mode(fixed, runtime_bound=False)
    fixed["agents"][0]["model_name"] = "openai/other"
    with pytest.raises(ValueError, match="REAL_CODEX_CONFIG_INVALID"):
        validate_agent_mode(fixed, runtime_bound=True)

    auth, bundle = tmp_path / "auth.json", tmp_path / "bundle"
    auth.write_text("{}")
    bundle.mkdir()
    environment = harbor_environment(auth_path=auth, bundle_root=bundle)
    assert {str(auth.resolve()), str(bundle.resolve())} <= set(environment.values())
    assert "CODEX_AUTH_JSON_PATH" not in environment


def test_harbor_entry_registers_the_guard_only_for_codex(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    guarded = type("Guarded", (), {})

    class Factory:
        @classmethod
        def get_agent_class(cls, name):
            return (cls, name)

    def load(name: str):
        if name == "harbor.agents.factory":
            return SimpleNamespace(AgentFactory=Factory)
        return SimpleNamespace(AgentName=SimpleNamespace(CODEX="codex"))

    monkeypatch.setattr(entry_module.importlib, "import_module", load)
    monkeypatch.setattr(entry_module, "guarded_codex_class", lambda **_kwargs: guarded)
    entry_module.register_guarded_codex(tmp_path / "auth", tmp_path / "bundle")
    assert Factory.get_agent_class("codex") is guarded
    assert Factory.get_agent_class("nop")[1] == "nop"
