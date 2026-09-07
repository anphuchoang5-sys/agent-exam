from __future__ import annotations

import json
import os
import subprocess
import uuid
from pathlib import Path

import pytest

from eval_platform.adapters.execution.harbor.config_mapper import HARBOR_REVISION
from eval_platform.adapters.execution.harbor.process_runner import run_bounded_process
from eval_platform.adapters.tasks.swe_gym import CANDIDATE_IMAGE

pytestmark = pytest.mark.integration
SIDECAR = "harbor-docker-egress-control-sidecar"


def test_fixed_harbor_network_policy_and_bypass_probes(tmp_path):
    if os.environ.get("AGENTEXAM_RUN_NETWORK_INTEGRATION") != "1":
        pytest.skip("Set AGENTEXAM_RUN_NETWORK_INTEGRATION=1 for the network probe")
    repo = Path(__file__).resolve().parents[4]
    tmp_path.resolve().relative_to(repo)
    revision = subprocess.check_output(
        ["git", "-C", str(repo / "framework/harbor"), "rev-parse", "HEAD"],
        text=True,
        timeout=10,
    ).strip()
    assert revision == HARBOR_REVISION
    project = f"agentexam-network-{uuid.uuid4().hex[:12]}"
    root = tmp_path / "network"
    root.mkdir(exist_ok=False)
    fixture_dir = root / "environment"
    fixture_dir.mkdir()
    (fixture_dir / "docker-compose.json").write_text(
        json.dumps(_definition(CANDIDATE_IMAGE)), encoding="utf-8"
    )
    _sidecar_source(repo, root)
    allowed = {
        "PATH",
        "PATHEXT",
        "SYSTEMROOT",
        "WINDIR",
        "COMSPEC",
        "TEMP",
        "TMP",
        "LOCALAPPDATA",
        "APPDATA",
        "USERPROFILE",
        "HOMEDRIVE",
        "HOMEPATH",
    }
    environment = {
        key: value for key, value in os.environ.items() if key.upper() in allowed
    }
    environment.update(
        PYTHONUTF8="1", PYTHONIOENCODING="utf-8", PYTHONDONTWRITEBYTECODE="1"
    )
    command = [
        str(repo / "framework/harbor/.venv/Scripts/python.exe"),
        str(Path(__file__).with_name("network_probe.py")),
        str(root),
        CANDIDATE_IMAGE,
        project,
    ]
    try:
        result = run_bounded_process(
            command,
            cwd=repo,
            env=environment,
            timeout_sec=600,
            evidence_root=root,
            max_log_bytes=1024 * 1024,
        )
        assert result.returncode == 0, f"Probe failed; inspect evidence at {root}"
        summary = json.loads((root / "summary.json").read_text())
        assert not summary["real_codex_ready"]
        failures = [
            row["name"]
            for row in summary["rows"]
            if not row["passed"] or not row.get("verified", True)
        ]
        assert not failures, f"Network safety failures: {failures}"
        facts = json.loads((root / "containers.json").read_text())
        assert len(facts) == 4
        for fact in facts:
            assert not fact["mounts"] and not fact["privileged"]
            assert fact["cap_drop"] == ["ALL"] and fact["pids_limit"] == 64
            assert fact["memory"] > 0 and fact["nano_cpus"] > 0
        main = next(fact for fact in facts if fact["name"].endswith("-main-1"))
        assert not main["cap_add"] and main["network_mode"].startswith("container:")
        assert "no-new-privileges:true" in main["security_opt"]
        assert not any(_resources(project).values()), "Harbor left project resources"
    finally:
        before = _resources(project)
        for kind, ids in before.items():
            if ids:
                args = ["docker", kind, "rm"]
                if kind in {"container", "image"}:
                    args.append("-f")
                subprocess.run(
                    [*args, *ids], check=True, capture_output=True, timeout=30
                )
        after = _resources(project)
        with (root / "cleanup.json").open("x", encoding="utf-8") as stream:
            json.dump(
                {
                    "project": project,
                    "before": before,
                    "remaining": after,
                    "verified": not any(after.values()),
                },
                stream,
                indent=2,
            )
        assert not any(after.values())


def _resources(project):
    result = {}
    for kind in ("container", "network", "volume", "image"):
        command = [
            "docker",
            kind,
            "ls",
            "-q",
            "--filter",
            f"label=com.docker.compose.project={project}",
        ]
        if kind == "container":
            command.append("--all")
        result[kind] = subprocess.check_output(command, text=True, timeout=10).split()
    return result


def _definition(image):
    common = {
        "cap_drop": ["ALL"],
        "security_opt": ["no-new-privileges:true"],
        "pids_limit": 64,
        "mem_limit": "128m",
        "cpus": 0.5,
    }
    services = {"main": {**common, "image": image}, SIDECAR: dict(common)}
    for name in ("allowed", "blocked"):
        services[name] = {
            **common,
            "image": image,
            "networks": {"default": {"aliases": [f"{name}.agentexam.test"]}},
            "command": [
                "sh",
                "-c",
                "mkdir -p /tmp/agentexam-www; "
                f"echo {name} > /tmp/agentexam-www/index.html; "
                "exec python -m http.server 8080 --directory /tmp/agentexam-www",
            ],
            "healthcheck": {
                "test": [
                    "CMD",
                    "python",
                    "-c",
                    "import urllib.request; "
                    "urllib.request.urlopen('http://127.0.0.1:8080', timeout=1)",
                ],
                "interval": "1s",
                "timeout": "2s",
                "retries": 10,
            },
        }
    return {"services": services}


def _sidecar_source(repo, root):
    """Export exact Git blobs so Windows checkout CRLF cannot alter scripts."""
    prefix = "src/harbor/environments/docker/" + SIDECAR
    for name in (
        "Dockerfile",
        "entrypoint.sh",
        "gost.yaml",
        "allowlist.txt",
        "bin/network-policy",
    ):
        data = subprocess.check_output(
            [
                "git",
                "-C",
                str(repo / "framework/harbor"),
                "show",
                f"{HARBOR_REVISION}:{prefix}/{name}",
            ],
            timeout=10,
        )
        destination = root / "sidecar-source" / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        with destination.open("xb") as stream:
            stream.write(data)
