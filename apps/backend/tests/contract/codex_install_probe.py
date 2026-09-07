"""Test-only installation contract: real Docker commands, no auth setup or model."""

from __future__ import annotations

import asyncio
import json
import subprocess
import sys
from pathlib import Path

from harbor.agents.installed.codex import Codex
from harbor.environments.base import ExecResult

from eval_platform.adapters.execution.codex_install import VERSION
from eval_platform.adapters.execution.harbor.config_mapper import HARBOR_REVISION
from eval_platform.adapters.tasks.swe_gym import CANDIDATE_IMAGE


def docker(*args, timeout=30):
    return subprocess.run(
        ["docker", *args], capture_output=True, text=True, check=True, timeout=timeout
    ).stdout.strip()


class InstalledContainer:
    """Only the exact upstream version command may reach this test environment."""

    def __init__(self, container):
        self.container = container
        self.commands = []

    async def exec(self, command, **kwargs):
        assert command == Codex._INSTALL_VERSION_COMMAND, "Online install forbidden"
        self.commands.append(command)
        return ExecResult(return_code=0, stdout=inside(self.container, command))


def inside(container, command):
    return docker(
        "exec",
        "--user",
        "65534:65534",
        "--workdir",
        "/tmp",
        container,
        "env",
        "-i",
        "HOME=/tmp/agentexam-home",
        "CODEX_HOME=/tmp/agentexam-codex-home",
        "PATH=/opt/agentexam-codex/bin:/opt/agentexam-codex/codex-path:/usr/bin:/bin",
        "/bin/sh",
        "-c",
        command,
    )


async def run(bundle, evidence, label):
    repo = Path(__file__).resolve().parents[4]
    revision = subprocess.check_output(
        ["git", "-C", str(repo / "framework/harbor"), "rev-parse", "HEAD"],
        text=True,
        timeout=10,
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
        timeout=10,
    ).strip()
    bundle.resolve().relative_to(evidence.resolve())
    assert len(label) == 32 and all(c in "0123456789abcdef" for c in label)
    selector = f"agentexam.installation_probe={label}"
    try:
        container = docker(
            "run",
            "--detach",
            "--pull=never",
            "--network",
            "none",
            "--name",
            f"agentexam-codex-install-{label[:12]}",
            "--label",
            selector,
            "--cap-drop",
            "ALL",
            "--security-opt",
            "no-new-privileges:true",
            "--cpus",
            "1",
            "--memory",
            "1g",
            "--memory-swap",
            "1g",
            "--pids-limit",
            "64",
            "--entrypoint",
            "/bin/sh",
            CANDIDATE_IMAGE,
            "-c",
            "sleep 600",
        )
        docker("exec", container, "mkdir", "-p", "/opt/agentexam-codex")
        docker(
            "cp", str(bundle) + "/.", container + ":/opt/agentexam-codex", timeout=90
        )
        docker("exec", container, "chmod", "-R", "a+rX", "/opt/agentexam-codex")
        docker(
            "exec",
            container,
            "chmod",
            "755",
            "/opt/agentexam-codex/bin/codex",
            "/opt/agentexam-codex/bin/codex-code-mode-host",
            "/opt/agentexam-codex/codex-path/rg",
            "/opt/agentexam-codex/codex-resources/bwrap",
            "/opt/agentexam-codex/codex-resources/zsh/bin/zsh",
        )
        version = inside(container, "codex --version")
        assert version == f"codex-cli {VERSION}"
        help_text = inside(container, "codex exec --help")
        assert "--ephemeral" in help_text and "--json" in help_text
        environment = InstalledContainer(container)
        agent = Codex(logs_dir=evidence, version=VERSION, reasoning_effort="medium")
        await agent.install(environment)
        assert environment.commands == [Codex._INSTALL_VERSION_COMMAND]
        obj = json.loads(docker("inspect", container))[0]
        host = obj["HostConfig"]
        facts = {
            "network": host["NetworkMode"],
            "mount_count": len(obj["Mounts"]),
            "cap_drop": host["CapDrop"],
            "cap_add": host["CapAdd"],
            "security_opt": host["SecurityOpt"],
            "privileged": host["Privileged"],
            "pids_limit": host["PidsLimit"],
            "memory": host["Memory"],
            "memory_swap": host["MemorySwap"],
            "nano_cpus": host["NanoCpus"],
            "base_image_id": obj["Image"],
        }
        assert facts["network"] == "none" and facts["mount_count"] == 0
        assert facts["cap_drop"] == ["ALL"] and not facts["cap_add"]
        assert not facts["privileged"] and facts["pids_limit"] == 64
        assert facts["memory"] == facts["memory_swap"] == 1024**3
        assert facts["nano_cpus"] == 1_000_000_000
        assert "no-new-privileges:true" in facts["security_opt"]
        no_auth = inside(
            container,
            "test ! -e /tmp/agentexam-codex-home/auth.json && "
            "test ! -e /tmp/codex-secrets && echo absent",
        )
        assert no_auth == "absent"
        with (evidence / "installation-result.json").open("x") as output:
            json.dump(
                {
                    "version": version,
                    "help_flags": ["--ephemeral", "--json"],
                    "harbor_reused_preinstalled": True,
                    "model_called": False,
                    "real_codex_ready": False,
                    "harbor_revision": revision,
                    "cli_uid": 65534,
                    "container": facts,
                },
                output,
                indent=2,
            )
    finally:
        ids = docker("ps", "-aq", "--filter", f"label={selector}").split()
        for identity in ids:
            docker("rm", "-f", identity)
        remaining = docker("ps", "-aq", "--filter", f"label={selector}")
        with (evidence / "installation-cleanup.json").open("x") as output:
            json.dump(
                {"removed": ids, "remaining": remaining, "verified": not remaining},
                output,
                indent=2,
            )
        assert not remaining


if __name__ == "__main__":
    asyncio.run(run(Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3]))
