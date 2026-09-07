from __future__ import annotations

import shlex

import pytest

from eval_platform.adapters.execution.codex_policy import (
    DENIED_PATHS,
    PROFILE,
    guarded_command,
    permission_config,
    prepare_workspace_command,
)


def original(instruction="repair the task"):
    return (
        "if [ -s ~/.nvm/nvm.sh ]; then . ~/.nvm/nvm.sh; fi; "
        "codex exec --dangerously-bypass-approvals-and-sandbox "
        "--skip-git-repo-check --model gpt-5.6-terra --json --enable unified_exec "
        "-c model_reasoning_effort=medium -c web_search=disabled -- "
        + shlex.quote(instruction)
        + " 2>&1 </dev/null | tee /logs/agent/codex.txt"
    )


def test_profile_is_fresh_closed_and_does_not_use_legacy_sandbox():
    config = permission_config("/testbed")
    assert config["default_permissions"] == PROFILE
    assert config["approval_policy"] == "never" and config["web_search"] == "disabled"
    assert not {"sandbox_mode", "sandbox_workspace_write"}.intersection(config)
    profile = config["permissions"][PROFILE]
    assert profile["network"] == {"enabled": False}
    assert profile["filesystem"]["/testbed"] == "write"
    for denied in DENIED_PATHS:
        assert profile["filesystem"][denied] == "deny"
    profile["filesystem"]["/tmp/codex-home"] = "write"
    assert permission_config("/testbed") != config


def test_prepare_workspace_requires_real_directory_and_preserves_deny_policy():
    command = prepare_workspace_command("/testbed")
    assert "test ! -L /testbed/.codex" in command
    assert command.endswith("mkdir -p /testbed/.codex")
    assert (
        permission_config("/testbed")["permissions"][PROFILE]["filesystem"][
            "/testbed/.codex"
        ]
        == "deny"
    )


@pytest.mark.parametrize(
    "path",
    [
        "/",
        "/tmp",
        "relative",
        "/testbed/",
        "/a/../b",
        "/logs/x",
        "/proc",
        "/tmp/codex-home",
        "/a;echo",
    ],
)
def test_bad_workspace_fails_closed(path):
    with pytest.raises(ValueError, match="CODEX_WORKSPACE_INVALID"):
        permission_config(path)


@pytest.mark.parametrize(
    "instruction",
    [
        "fix",
        "",
        "'; echo injected; #",
        "instructions mention --dangerously-bypass-approvals-and-sandbox\nand 'quotes'",
    ],
)
def test_fixed_launch_replaces_flags_not_instruction(instruction):
    result = guarded_command(original(instruction), "gpt-5.6-terra", "medium")
    flags, body = result.split(" -- ", 1)
    assert result.startswith("codex exec ")
    assert "bypass" not in flags and "nvm" not in flags
    assert (
        body
        == shlex.quote(instruction) + " 2>&1 </dev/null | tee /logs/agent/codex.txt"
    )


@pytest.mark.parametrize(
    "before,after",
    [
        ("exec ", "exec resume --last "),
        ("medium", "medium --sandbox danger-full-access"),
        ("web_search=disabled", "web_search=live"),
        ("codex.txt", "other.txt"),
        ("--json ", "--json --full-auto "),
    ],
)
def test_upstream_command_drift_is_not_silently_executed(before, after):
    with pytest.raises(ValueError, match="CODEX_UPSTREAM_COMMAND_MISMATCH"):
        guarded_command(original().replace(before, after, 1), "gpt-5.6-terra", "medium")


@pytest.mark.parametrize(
    "model,effort", [("x;echo", "medium"), ("gpt-5.6-terra", "medium;echo")]
)
def test_runtime_shell_injection_rejected(model, effort):
    with pytest.raises(ValueError, match="CODEX_RUNTIME_CONFIG_INVALID"):
        guarded_command(original(), model, effort)
