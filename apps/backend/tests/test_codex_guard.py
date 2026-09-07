from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from eval_platform.adapters.execution.harbor_entry import harbor_environment


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
from eval_platform.adapters.execution.codex_agent import guarded_codex_class
from eval_platform.adapters.execution.codex_install import VERSION
Guard = guarded_codex_class()
kwargs = dict(logs_dir=Path.cwd(), version=VERSION, reasoning_effort="medium",
              model_name="openai/gpt-5.6-terra")
for field, value in (("config", "must-not-read"), ("extra_env", {}),
                     ("mcp_servers", []), ("version", "latest"),
                     ("reasoning_effort", None)):
    try:
        Guard(**{**kwargs, field: value})
    except ValueError as error:
        assert str(error) == "CODEX_GUARD_CONFIG_INVALID"
    else:
        raise AssertionError(field)
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
