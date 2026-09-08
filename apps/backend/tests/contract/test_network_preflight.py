from __future__ import annotations

import json
import subprocess

import pytest

import prototype_codex_harbor_e2e as prototype
from eval_platform.adapters.execution import preflight
from eval_platform.adapters.execution.network import _adapt_dns_policy
from eval_platform.adapters.tasks.swe_gym import CANDIDATE_IMAGE

pytestmark = pytest.mark.contract


@pytest.mark.parametrize(
    "scenario,expected",
    [
        ("supported", "SUPPORTED_KERNEL"),
        ("unsupported", "UNSUPPORTED_KERNEL"),
        ("unknown", "KERNEL_CAPABILITY_UNKNOWN"),
        ("bad_output", "PROBE_PROTOCOL_ERROR"),
        ("nonzero", "PROBE_PROCESS_FAILED"),
        ("timeout", "PROBE_PROCESS_FAILED"),
        ("absent", "DOCKER_UNAVAILABLE"),
        ("cleanup_error", "PROBE_CLEANUP_UNVERIFIED"),
    ],
)
def test_offline_probe_is_bounded_owned_and_fail_closed(
    tmp_path, monkeypatch, scenario, expected
):
    calls = []
    query_count = 0
    container = "a" * 12

    def run(command, **kwargs):
        nonlocal query_count
        calls.append(command)
        assert kwargs["timeout"] <= 30 and kwargs["capture_output"]
        if command[:2] == ["docker", "run"]:
            assert command[command.index("--network") + 1] == "none"
            assert command[command.index("--cap-drop") + 1] == "ALL"
            assert command[command.index("--memory") + 1] == "64m"
            assert command[command.index("--pids-limit") + 1] == "32"
            assert "--pull=never" in command and "--read-only" in command
            assert "--rm" in command and CANDIDATE_IMAGE in command
            assert not set(command).intersection(
                {"--mount", "--volume", "--privileged"}
            )
            if scenario == "absent":
                raise FileNotFoundError("DO_NOT_PERSIST")
            if scenario == "timeout":
                raise subprocess.TimeoutExpired(command, 30)
            capability = (
                scenario
                if scenario in {"supported", "unsupported", "unknown"}
                else "supported"
            )
            output = f"KERNEL=5.15.0-test\nNFT_FIB_INET={capability}\n"
            if scenario == "bad_output":
                output = "DO_NOT_PERSIST"
            return subprocess.CompletedProcess(
                command, int(scenario == "nonzero"), output, "DO_NOT_PERSIST"
            )
        if command[:3] == ["docker", "ps", "-aq"]:
            query_count += 1
            name = calls[0][calls[0].index("--name") + 1]
            assert f"name=^/{name}$" in command
            assert f"label=agentexam.network.preflight={name}" in command
            if scenario == "cleanup_error":
                raise subprocess.CalledProcessError(1, command)
            output = container if scenario == "timeout" and query_count == 1 else ""
            return subprocess.CompletedProcess(command, 0, output)
        assert command == ["docker", "rm", "-f", container]
        return subprocess.CompletedProcess(command, 0, "")

    monkeypatch.setattr(preflight.subprocess, "run", run)
    directory = tmp_path / "new-evidence"
    result = preflight.network_preflight(directory)
    assert result["status"] == expected
    assert result["real_codex_ready"] is False
    assert result["cleanup"]["verified"] is (scenario != "cleanup_error")
    text = (directory / "network-preflight.json").read_text()
    assert "DO_NOT_PERSIST" not in text
    if scenario == "timeout":
        assert result["cleanup"]["removed_ids"] == [container]
    if scenario == "cleanup_error":
        assert result["probe_status"] == "SUPPORTED_KERNEL"
    assert json.loads(text)["status"] == expected
    before = len(calls)
    with pytest.raises(FileExistsError):
        preflight.network_preflight(directory)
    assert len(calls) == before


@pytest.mark.parametrize(
    "status",
    [
        "UNSUPPORTED_KERNEL",
        "KERNEL_CAPABILITY_UNKNOWN",
        "PROBE_PROCESS_FAILED",
        "PROBE_CLEANUP_UNVERIFIED",
        "SUPPORTED_KERNEL",
    ],
)
def test_cli_never_marks_kernel_check_as_real_codex_acceptance(
    monkeypatch, capsys, status
):
    monkeypatch.setattr("sys.argv", ["prototype", "--check-network"])
    monkeypatch.setattr(
        prototype, "task_preflight", lambda _: {"real_codex_ready": False}
    )
    monkeypatch.setattr(prototype, "network_preflight", lambda _: {"status": status})
    assert prototype.main() == (0 if status == "SUPPORTED_KERNEL" else 2)
    report = json.loads(capsys.readouterr().out)
    assert report["real_codex_ready"] is False


def test_task_only_preflight_does_not_touch_docker(monkeypatch, capsys):
    monkeypatch.setattr("sys.argv", ["prototype", "--check"])
    monkeypatch.setattr(
        prototype, "task_preflight", lambda _: {"real_codex_ready": False}
    )
    monkeypatch.setattr(
        prototype, "network_preflight", lambda _: pytest.fail("Docker called")
    )
    assert prototype.main() == 0
    assert "network" not in json.loads(capsys.readouterr().out)


@pytest.mark.parametrize(
    "anchor", [b"setup_nftables() {\n", b"$(nft_dns_rules accept)\n"]
)
@pytest.mark.parametrize("count", [0, 2])
def test_dns_adaptation_rejects_missing_or_ambiguous_source(anchor, count):
    data = b"setup_nftables() {\n$(nft_dns_rules accept)\n"
    with pytest.raises(ValueError, match="HARBOR_DNS_POLICY_SOURCE_UNSUPPORTED"):
        _adapt_dns_policy(data.replace(anchor, anchor * count))
