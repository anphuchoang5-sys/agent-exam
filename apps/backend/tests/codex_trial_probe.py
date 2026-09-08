"""Internal fixed-Harbor Job driver. Never used by the production entrypoint."""

from __future__ import annotations

import asyncio
import hashlib
import json
import subprocess
import sys
from pathlib import Path

from harbor.agents.factory import AgentFactory
from harbor.environments.docker.docker import DockerEnvironment
from harbor.job import Job
from harbor.models.job.config import JobConfig

from eval_platform.adapters.execution.codex.agent import guarded_codex_class
from eval_platform.adapters.execution.codex.install import VERSION
from eval_platform.adapters.execution.harbor.config_mapper import HARBOR_REVISION
from eval_platform.adapters.execution.harbor_entry import validate_network_config
from eval_platform.adapters.execution.network import export_sidecar


async def main(root, bundle_root, mode):
    config = json.loads((root / "config.json").read_text())
    assert config["agents"] == [
        {
            "name": "codex",
            "model_name": "openai/gpt-5.6-terra",
            "n_concurrent": 1,
            "kwargs": {
                "version": VERSION,
                "reasoning_effort": "medium",
                "web_search": "disabled",
            },
        }
    ]
    validate_network_config(config)
    repo = Path(__file__).resolve().parents[3]
    context = root / "sidecar-source"
    export_sidecar(repo / "framework/harbor", context, HARBOR_REVISION)
    DockerEnvironment._EGRESS_CONTROL_SIDECAR_CONTEXT_PATH = context
    manifest = json.loads((bundle_root / "installation-input.json").read_text())
    assert manifest["version"] == VERSION and len(manifest["files_sha256"]) == 8
    for name, digest in manifest["files_sha256"].items():
        with (bundle_root / name).open("rb") as source:
            assert hashlib.file_digest(source, "sha256").hexdigest() == digest
    bundle = bundle_root / "package/vendor/x86_64-unknown-linux-musl"
    auth = root / "synthetic-auth.json"
    auth.write_text(
        json.dumps(
            {
                "tokens": {
                    "access_token": "AGENTEXAM-SYNTHETIC-ORIGINAL-ONLY",
                    "refresh_token": "AGENTEXAM-SYNTHETIC-REFRESH-TOKEN-ONLY",
                }
            }
        )
    )
    (root / "mode").write_text(mode)
    (root / "codex").write_text(
        '#!/bin/sh\nexec /usr/bin/python3 /opt/agentexam-fixture.py "$@"\n',
        newline="\n",
    )
    observations = []

    class SyntheticCodex(guarded_codex_class()):
        def __init__(self, **kwargs):
            super().__init__(**kwargs)
            self._probe_auth = auth

        def _resolve_auth_json_path(self):
            return self._probe_auth

        async def setup(self, environment):
            await environment.upload_dir(bundle, "/opt/agentexam-codex")
            await environment.upload_file(
                Path(__file__).with_name("codex_trial_fixture.py"),
                "/opt/agentexam-fixture.py",
            )
            await environment.upload_file(root / "mode", "/opt/agentexam-mode")
            await self.exec_as_root(
                environment,
                command=(
                    "chmod 0555 /opt/agentexam-codex/bin/* "
                    "/opt/agentexam-codex/codex-resources/bwrap "
                    "/opt/agentexam-codex/codex-resources/zsh/bin/zsh "
                    "/opt/agentexam-codex/codex-path/rg"
                ),
            )
            result = await environment.exec("/opt/agentexam-codex/bin/codex --version")
            (root / "version-check.json").write_text(
                json.dumps(
                    {
                        "return_code": result.return_code,
                        "stdout": result.stdout,
                        "stderr": result.stderr,
                    },
                    indent=2,
                )
            )
            assert result.return_code == 0
            assert result.stdout.splitlines()[-1] == "codex-cli " + VERSION
            await self.exec_as_root(
                environment,
                command=(
                    "mv /opt/agentexam-codex/bin/codex "
                    "/opt/agentexam-codex/bin/codex-real"
                ),
            )
            await environment.upload_file(
                root / "codex", "/opt/agentexam-codex/bin/codex"
            )
            await self.exec_as_root(
                environment,
                command="chmod 0555 /opt/agentexam-codex/bin/codex",
            )

        async def run(self, instruction, environment, context):
            identity = await environment._run_docker_compose_command(
                ["ps", "-q", "main"]
            )
            obj = json.loads(
                subprocess.check_output(
                    ["docker", "inspect", identity.stdout.strip()], timeout=30
                )
            )[0]
            host = obj["HostConfig"]
            assert host["CapDrop"] == ["ALL"] and not host["CapAdd"]
            assert (
                not host["Privileged"]
                and "no-new-privileges:true" in host["SecurityOpt"]
            )
            assert host["PidsLimit"] == 64 and host["Memory"] == 2048 * 1024 * 1024
            mounts = sorted(item["Destination"] for item in obj["Mounts"])
            assert mounts == ["/logs/agent", "/logs/artifacts", "/logs/verifier"]
            (root / "container-boundary.json").write_text(
                json.dumps(
                    {
                        "container_id": obj["Id"],
                        "mount_destinations": mounts,
                        "capabilities_dropped": host["CapDrop"],
                        "pids_limit": host["PidsLimit"],
                        "memory_bytes": host["Memory"],
                        "network_mode": host["NetworkMode"],
                    },
                    indent=2,
                )
            )
            observations.append({"user": environment.default_user, "mode": mode})
            try:
                await super().run(instruction, environment, context)
            finally:
                result = await environment.exec(
                    "test ! -e /tmp/codex-home && test ! -e /tmp/codex-secrets"
                )
                observations[-1]["credential_directories_removed"] = (
                    result.return_code == 0
                )

    original = AgentFactory.get_agent_class
    AgentFactory.get_agent_class = classmethod(lambda cls, name: SyntheticCodex)
    try:
        job = await Job.create(JobConfig.model_validate(config))
        await job.run()
    finally:
        AgentFactory.get_agent_class = original
        (root / "probe-observations.json").write_text(
            json.dumps(
                {
                    "real_codex_ready": False,
                    "model_called": False,
                    "observations": observations,
                },
                indent=2,
            )
        )


if __name__ == "__main__":
    assert sys.argv[3] in {"success", "failure", "timeout", "patch-secret"}
    asyncio.run(main(Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3]))
