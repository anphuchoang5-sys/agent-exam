"""Test-only installation contract: real Docker commands, no auth setup or model."""

from __future__ import annotations

import asyncio
import json
import subprocess
import sys
from pathlib import Path

from harbor.environments.base import ExecResult

from eval_platform.adapters.execution.codex.agent import guarded_codex_class
from eval_platform.adapters.execution.codex.install import (
    INSTALL_COMMAND,
    INSTALL_ROOT,
    PREPARE_INSTALL_COMMAND,
    VERSION,
)
from eval_platform.adapters.execution.harbor.config_mapper import HARBOR_REVISION
from eval_platform.adapters.tasks.swe_gym import CANDIDATE_IMAGE


def docker(*args, timeout=30):
    return subprocess.run(
        ["docker", *args], capture_output=True, text=True, check=True, timeout=timeout
    ).stdout.strip()


def git(repo, *args):
    return subprocess.check_output(
        ["git", "-C", str(repo), *args], text=True, timeout=10
    ).strip()


def inside(container, command, *, user="65534:65534", env=None, check=True):
    variables = {
        "HOME": "/nonexistent",
        "CODEX_HOME": "/tmp/agentexam-codex-home",
        "PATH": "/opt/agentexam-codex/bin:/opt/agentexam-codex/codex-path:"
        "/usr/bin:/bin",
        **(env or {}),
    }
    result = subprocess.run(
        [
            "docker",
            "exec",
            *f"--user {user} --workdir /tmp".split(),
            container,
            *"env -i".split(),
            *(f"{key}={value}" for key, value in variables.items()),
            *("/bin/bash", "-lc", command),
        ],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    if check:
        result.check_returncode()
    return result


class InstalledContainer:
    default_user = "65534:65534"

    def __init__(self, container):
        self.container = container
        self.commands = []

    async def exec(self, command, **kwargs):
        plain = command.removeprefix("set -o pipefail; ")
        allowed = {PREPARE_INSTALL_COMMAND, INSTALL_COMMAND}
        assert plain in allowed or plain.endswith("codex --version"), (
            "Online install forbidden"
        )
        self.commands.append(command)
        user = kwargs.get("user") or self.default_user
        result = inside(
            self.container,
            command,
            user=str(user),
            env=kwargs.get("env"),
            check=False,
        )
        return ExecResult(
            return_code=result.returncode,
            stdout=result.stdout,
            stderr=result.stderr,
        )

    async def upload_dir(self, source, target):
        assert target == INSTALL_ROOT
        docker("cp", str(source) + "/.", self.container + ":" + target, timeout=90)


async def run(bundle_root, evidence, label):
    repo = Path(__file__).resolve().parents[4]
    harbor = repo / "framework/harbor"
    revision = git(harbor, "rev-parse", "HEAD")
    assert revision == HARBOR_REVISION
    assert not git(harbor, "status", "--porcelain", "--untracked-files=no")
    bundle_root.resolve().relative_to(evidence.resolve())
    assert len(label) == 32 and all(c in "0123456789abcdef" for c in label)
    selector = f"agentexam.installation_probe={label}"
    try:
        options = (
            f"--detach --pull=never --network none --name "
            f"agentexam-codex-install-{label[:12]} --label {selector} "
            "--cap-drop ALL --security-opt no-new-privileges:true --cpus 1 "
            "--memory 1g --memory-swap 1g --pids-limit 64"
        ).split()
        container = docker(
            "run",
            *options,
            "--entrypoint",
            "/bin/sh",
            CANDIDATE_IMAGE,
            "-c",
            "sleep 600",
        )
        auth = evidence / "synthetic-auth.json"
        auth.write_text("{}")
        environment = InstalledContainer(container)
        agent_class = guarded_codex_class(auth_path=auth, bundle_root=bundle_root)
        agent = agent_class(
            logs_dir=evidence,
            model_name="openai/gpt-5.6-terra",
            version=VERSION,
            reasoning_effort="medium",
        )
        await agent.install(environment)
        version = f"codex-cli {VERSION}"
        assert version in inside(container, "codex --version").stdout.splitlines()
        help_text = inside(container, "codex exec --help").stdout
        assert "--ephemeral" in help_text and "--json" in help_text
        assert len(environment.commands) == 3
        assert not any(
            "curl" in command or "npm" in command for command in environment.commands
        )
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
        ).stdout.strip()
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
