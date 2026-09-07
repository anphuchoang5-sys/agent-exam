"""Test-only driver for the fixed Harbor environment; never a real Agent."""

from __future__ import annotations

import asyncio
import json
import shlex
import subprocess
import sys
from pathlib import Path

from harbor.environments.docker.docker import DockerEnvironment
from harbor.models.task.config import EnvironmentConfig, NetworkPolicy
from harbor.models.trial.paths import TrialPaths

SIDECAR = "harbor-docker-egress-control-sidecar"
CURL = (
    "env -u HTTP_PROXY -u HTTPS_PROXY -u ALL_PROXY -u http_proxy "
    "-u https_proxy -u all_proxy curl -sS --noproxy '*' "
    "--connect-timeout 3 --max-time 6 "
)


def save(root, name, value):
    with (root / f"{name}.json").open("x", encoding="utf-8") as stream:
        json.dump(value, stream, indent=2)


async def run(root, image, project):
    DockerEnvironment._EGRESS_CONTROL_SIDECAR_CONTEXT_PATH = root / "sidecar-source"
    environment = root / "environment"
    compose_path = environment / "docker-compose.json"
    compose = json.loads(compose_path.read_text(encoding="utf-8"))
    assert all(
        compose["services"][name]["image"] == image for name in ("allowed", "blocked")
    )
    paths = TrialPaths(root / "trial")
    paths.mkdir()
    policy = NetworkPolicy(
        network_mode="allowlist", allowed_hosts=["allowed.agentexam.test"]
    )
    env = DockerEnvironment(
        environment_dir=environment,
        environment_name=project,
        session_id=project,
        trial_paths=paths,
        task_env_config=EnvironmentConfig(docker_image=image),
        network_policy=policy,
        mounts=[],
        extra_docker_compose=[compose_path],
        override_cpus=1,
        override_memory_mb=256,
    )
    rows = []
    addresses = {}

    async def probe(name, command, expectation):
        result = await env.exec(command, timeout_sec=12)
        body = (result.stdout or "").strip()
        success = result.return_code == 0
        denied = result.return_code in {7, 28, 52, 56}
        if expectation in {"allowed", "blocked"}:
            matched = body == expectation and success
        elif expectation == "denied":
            matched = denied
        elif expectation == "permission-denied":
            matched = result.return_code == 1 and "PermissionError" in body
        else:
            assert expectation == "not-blocked-target"
            matched = denied or (body == "allowed" and success)
        row = {
            "name": name,
            "returncode": result.return_code,
            "stdout": body[:256],
            "stdout_truncated": len(body) > 256,
            "expectation": expectation,
            "passed": matched,
        }
        save(root, name, row)
        rows.append(row)
        return row

    def request(target):
        hostname = f"{target}.agentexam.test"
        resolve = (
            f"--resolve {hostname}:8080:{addresses[hostname]} " if addresses else ""
        )
        return CURL + resolve + f"http://{hostname}:8080"

    async def targets(stage, permitted):
        for target in ("allowed", "blocked"):
            expectation = target if target in permitted else "denied"
            await probe(f"{stage}-{target}", request(target), expectation)

    try:
        await env.start(force_build=False)
        await targets("initial", {"allowed"})
        await env.set_network_policy(NetworkPolicy(network_mode="public"))
        hosts = [f"{name}.agentexam.test" for name in ("allowed", "blocked")]
        hosts += ["host.docker.internal", "http.docker.internal"]
        lookup = "import socket,json; print(json.dumps({h:socket.gethostbyname(h) "
        lookup += f"for h in {hosts!r}" + "}))"
        resolved = await env.exec("python -c " + shlex.quote(lookup), timeout_sec=12)
        assert resolved.return_code == 0, "Cannot establish IPv4 positive controls"
        addresses = json.loads(resolved.stdout)
        save(root, "addresses", addresses)
        await targets("control", {"allowed", "blocked"})
        proxy_commands = {
            "host-proxy": f"{addresses['host.docker.internal']}:7890",
            "desktop-proxy": f"{addresses['http.docker.internal']}:3128",
        }
        controls = {}
        for name, proxy in proxy_commands.items():
            command = CURL.replace(
                "--noproxy '*'", f"--noproxy '' --proxy http://{proxy}"
            )
            command += "--fail --head --output /dev/null https://example.com/"
            result = await env.exec(command, timeout_sec=12)
            controls[name] = (command, result.return_code)
        await env.set_network_policy(policy)
        await targets("allowlist", {"allowed"})
        await probe(
            "spoofed-host",
            request("blocked") + " -H 'Host: allowed.agentexam.test:8080'",
            "not-blocked-target",
        )
        mark = (
            "import socket; socket.socket().setsockopt(socket.SOL_SOCKET, 36, 114514)"
        )
        await probe(
            "socket-mark", "python -c " + shlex.quote(mark), "permission-denied"
        )
        for name, (command, code) in controls.items():
            row = await probe(name, command, "denied")
            row["control_returncode"] = code
            row["verified"] = code == 0 and row["passed"]
        save(root, "proxy-controls", rows[-2:])
        await env.set_network_policy(NetworkPolicy(network_mode="no-network"))
        await targets("deny-all", set())
        await env.set_network_policy(policy)
        await targets("recovered", {"allowed"})
        await env.stop_service(SIDECAR)
        await targets("sidecar-stop", set())
        save(
            root,
            "summary",
            {"prototype": True, "real_codex_ready": False, "rows": rows},
        )
    finally:
        ids = subprocess.run(
            [
                "docker",
                "ps",
                "-aq",
                "--filter",
                f"label=com.docker.compose.project={project}",
            ],
            capture_output=True,
            text=True,
            timeout=10,
            check=True,
        ).stdout.split()
        facts = []
        for identity in ids:
            obj = json.loads(
                subprocess.check_output(["docker", "inspect", identity], timeout=10)
            )[0]
            host = obj["HostConfig"]
            facts.append(
                {
                    "id": identity,
                    "image": obj["Image"],
                    "name": obj["Name"],
                    "cap_drop": host["CapDrop"],
                    "cap_add": host["CapAdd"],
                    "network_mode": host["NetworkMode"],
                    "mounts": obj["Mounts"],
                    "privileged": host["Privileged"],
                    "memory": host["Memory"],
                    "nano_cpus": host["NanoCpus"],
                    "pids_limit": host["PidsLimit"],
                    "security_opt": host["SecurityOpt"],
                }
            )
        save(root, "containers", facts)
        await asyncio.wait_for(env.stop(delete=True), timeout=45)


if __name__ == "__main__":
    asyncio.run(run(Path(sys.argv[1]), sys.argv[2], sys.argv[3]))
