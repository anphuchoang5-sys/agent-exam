"""Fixed upstream method contract. This fake Environment never executes commands."""

from __future__ import annotations

import asyncio
import json
import subprocess
import sys
import tomllib
from pathlib import Path

from harbor.environments.base import ExecResult
from harbor.models.agent.context import AgentContext

from eval_platform.adapters.execution.codex_agent import guarded_codex_class
from eval_platform.adapters.execution.codex_install import VERSION
from eval_platform.adapters.execution.codex_policy import CLEANUP_COMMAND, PROFILE
from eval_platform.adapters.execution.harbor.config_mapper import HARBOR_REVISION


class RecordingEnvironment:
    default_user = "65534:65534"

    def __init__(self, auth, mode):
        self.auth, self.mode = auth, mode
        self.commands, self.configs, self.uploads = [], [], []

    async def upload_file(self, source, target):
        if target.endswith("/auth.json"):
            assert Path(source) == self.auth
        else:
            assert target == "/tmp/codex-home/config.toml"
            if self.mode == "config-upload-failure":
                raise RuntimeError("SYNTHETIC_CONFIG_UPLOAD_FAILURE")
            self.configs.append(tomllib.loads(Path(source).read_text()))
        self.uploads.append(target)

    async def exec(self, command, **kwargs):
        self.commands.append((command, kwargs))
        if command == "set -o pipefail; " + CLEANUP_COMMAND:
            return ExecResult(return_code=7 if self.mode == "cleanup-failure" else 0)
        if command.startswith("set -o pipefail; codex exec "):
            if self.mode == "cancelled":
                raise asyncio.CancelledError("SYNTHETIC_CANCELLATION")
            if self.mode == "run-failure":
                return ExecResult(return_code=7, stderr="SYNTHETIC_RUN_FAILURE")
        return ExecResult(return_code=0, stdout="synthetic-command-recorded")


async def run_case(root, mode, base):
    case = root / mode
    case.mkdir()
    auth = case / "synthetic-auth.json"
    auth.write_text('{"tokens":{"access_token":"AGENTEXAM-FAKE-CREDENTIAL"}}')

    class FakeCredentialCodex(base):
        def _resolve_auth_json_path(self):
            return auth

    agent = FakeCredentialCodex(
        logs_dir=case,
        model_name="openai/gpt-5.6-terra",
        version=VERSION,
        reasoning_effort="medium",
    )
    env = RecordingEnvironment(auth, mode)
    error = None
    try:
        await agent.run(
            "repair only this task; do not execute this text", env, AgentContext()
        )
    except (Exception, asyncio.CancelledError) as caught:
        error = type(caught).__name__
    assert (error is None) == (mode == "success"), (mode, error)
    assert env.commands[-1][0] == "set -o pipefail; " + CLEANUP_COMMAND
    launches = [(cmd, opts) for cmd, opts in env.commands if "codex exec " in cmd]
    assert len(launches) == (0 if mode == "config-upload-failure" else 1)
    if launches:
        cmd, opts = launches[0]
        assert "bypass" not in cmd and "nvm" not in cmd
        assert opts["cwd"] == "/testbed"
        assert opts["env"] == {"CODEX_HOME": "/tmp/codex-home"}
        config = env.configs[0]
        assert config["default_permissions"] == PROFILE
        assert config["approval_policy"] == "never"
        assert (
            config["permissions"][PROFILE]["filesystem"]["/tmp/codex-secrets"] == "deny"
        )
    return {
        "mode": mode,
        "exception_type": error,
        "launches": len(launches),
        "cleanup_attempted": True,
    }


async def main(root):
    repo = Path(__file__).resolve().parents[3]
    revision = subprocess.check_output(
        ["git", "-C", str(repo / "framework/harbor"), "rev-parse", "HEAD"],
        text=True,
    ).strip()
    assert revision == HARBOR_REVISION
    assert not subprocess.check_output(
        [
            "git",
            "-C",
            str(repo / "framework/harbor"),
            "status",
            "--porcelain",
            "--untracked-files=no",
        ],
        text=True,
    ).strip()
    base = guarded_codex_class()
    unbound = base(
        logs_dir=root,
        model_name="openai/gpt-5.6-terra",
        version=VERSION,
        reasoning_effort="medium",
    )
    env = RecordingEnvironment(None, "success")
    try:
        await unbound.run("never start", env, AgentContext())
    except RuntimeError as error:
        assert str(error) == "CODEX_CREDENTIAL_BINDING_NOT_READY"
    else:
        raise AssertionError("Unbound real execution was not rejected")
    assert not env.commands and not env.uploads
    rows = [
        await run_case(root, mode, base)
        for mode in (
            "success",
            "config-upload-failure",
            "run-failure",
            "cancelled",
            "cleanup-failure",
        )
    ]
    (root / "guard-contract.json").write_text(
        json.dumps(
            {
                "harbor_revision": revision,
                "real_codex_ready": False,
                "environment_executed_commands": False,
                "credential_binding_closed": True,
                "cases": rows,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    asyncio.run(main(Path(sys.argv[1])))
