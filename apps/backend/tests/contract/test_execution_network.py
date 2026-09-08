from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

import pytest

from eval_platform.adapters.execution.harbor.config_mapper import (
    HARBOR_REVISION,
    build_job_plan,
)
from eval_platform.adapters.execution.harbor_entry import (
    harbor_command,
    harbor_environment,
    validate_agent_mode,
    validate_network_config,
)
from eval_platform.adapters.execution.network import (
    SIDECAR,
    compose_profile,
    export_sidecar,
    validate_hosts,
)
from eval_platform.adapters.tasks.swe_gym import render_harbor_task
from eval_platform.application.ports.execution import RunLimits

pytestmark = pytest.mark.contract


@pytest.mark.parametrize(
    "host",
    [
        "*",
        "*.example.com",
        "https://example.com",
        "example.com:443",
        "127.0.0.1",
        "::1",
        "host.docker.internal",
        "http.docker.internal",
        "localhost",
        "a.local",
        "a..com",
        "-a.com",
        "a.com\nblocked.com",
        "a.com/path",
        "a.com@b.com",
    ],
)
def test_only_exact_registered_dns_names_are_accepted(host):
    with pytest.raises(ValueError):
        validate_hosts((host,))


def test_policy_is_deterministic_and_never_adds_a_public_default():
    assert validate_hosts(()) == ()
    assert validate_hosts(("B.example.com", "a.example.com", "a.example.com")) == (
        "a.example.com",
        "b.example.com",
    )
    profile = compose_profile(RunLimits(30, 2, 1024, 4096))
    main = profile["services"]["main"]
    assert main["cap_drop"] == ["ALL"]
    assert main["pids_limit"] == 64 and main["cpus"] == 2
    assert main["mem_limit"] == main["memswap_limit"] == "1024m"
    assert "network_mode" not in main and "networks" not in main
    assert "volumes" not in main and "ports" not in main
    assert not main["environment"]["HTTP_PROXY"]


def test_environment_excludes_credentials_and_untrusted_python_settings(monkeypatch):
    for name in ("OPENAI_API_KEY", "CODEX_AUTH_JSON_PATH", "HTTPS_PROXY", "PYTHONPATH"):
        monkeypatch.setenv(name, "sensitive-sentinel-do-not-copy")
    result = harbor_environment()
    assert "sensitive-sentinel-do-not-copy" not in json.dumps(result)
    assert result["HARBOR_TELEMETRY"] == "disabled"
    assert Path(result["PYTHONPATH"]).name == "src"


def test_real_agents_are_blocked_before_importing_or_running_harbor():
    assert (
        validate_agent_mode(
            {"agents": [{"name": "nop", "n_concurrent": 1}]},
            runtime_bound=False,
        )
        == "nop"
    )
    for agents in ([], [{"name": "codex"}], [{"name": "nop", "import_path": "x:y"}]):
        with pytest.raises(ValueError, match="REAL_CODEX_CONFIG_INVALID"):
            validate_agent_mode({"agents": agents}, runtime_bound=False)


def test_command_uses_the_configured_harbor_python(tmp_path):
    executable = tmp_path / "harbor/.venv/Scripts/harbor.exe"
    executable.parent.mkdir(parents=True)
    executable.touch()
    python = executable.with_name("python.exe")
    with pytest.raises(FileNotFoundError):
        harbor_command(executable, tmp_path / "job.json")
    python.touch()
    command = harbor_command(executable, tmp_path / "job.json")
    assert command[0] == str(python.resolve())
    assert Path(command[1]).name == "harbor_entry.py"
    assert command[2:4] == ["--config", str((tmp_path / "job.json").resolve())]


def test_bootstrap_imports_fixed_harbor_not_the_adjacent_adapter_package():
    from eval_platform.adapters.execution import harbor_entry

    repo = Path(__file__).resolve().parents[4]
    python = repo / "framework/harbor/.venv/Scripts/python.exe"
    result = subprocess.run(
        [str(python), "-c", "import harbor; print(harbor.__file__)"],
        cwd=Path(harbor_entry.__file__).parent,
        env=harbor_environment(),
        check=True,
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert (
        Path(result.stdout.strip()).resolve()
        == (repo / "framework/harbor/src/harbor/__init__.py").resolve()
    )


def test_sidecar_exports_traceable_dns_adaptation_and_never_overwrites(tmp_path):
    repo = Path(__file__).resolve().parents[4] / "framework/harbor"
    destination = tmp_path / "sidecar-source"
    export_sidecar(repo, destination, HARBOR_REVISION)
    assert (destination / "entrypoint.sh").read_bytes().startswith(b"#!/bin/sh\n")
    manifest = json.loads((tmp_path / "network-source.json").read_text())
    assert manifest["revision"] == HARBOR_REVISION and len(manifest["sha256"]) == 5
    assert manifest["adaptation"] == "docker-desktop-dns-192.168.65.7-udp53-v1"
    for name, digest in manifest["sha256"].items():
        assert hashlib.sha256((destination / name).read_bytes()).hexdigest() == digest
        source = f"{HARBOR_REVISION}:src/harbor/environments/docker/{SIDECAR}/{name}"
        original = subprocess.check_output(
            ["git", "-C", str(repo), "show", source], timeout=10
        )
        upstream = manifest["upstream_sha256"][name]
        assert hashlib.sha256(original).hexdigest() == upstream
        assert (digest != upstream) == (name == "bin/network-policy")
    with pytest.raises(FileExistsError):
        export_sidecar(repo, destination, HARBOR_REVISION)


@pytest.mark.parametrize("dirty", [False, True])
def test_source_mismatch_or_dirty_checkout_is_rejected(tmp_path, monkeypatch, dirty):
    def fake_run(command, **kwargs):
        output = HARBOR_REVISION if "rev-parse" in command and dirty else "bad"
        return subprocess.CompletedProcess(command, 0, stdout=output.encode())

    monkeypatch.setattr(
        "eval_platform.adapters.execution.network.subprocess.run", fake_run
    )
    with pytest.raises(ValueError, match="HARBOR_SOURCE_NOT_FIXED"):
        export_sidecar(tmp_path, tmp_path / "new", HARBOR_REVISION)
    assert not (tmp_path / "new").exists()


@pytest.mark.parametrize("tamper", [None, "baseline", "phase", "compose", "extra"])
def test_runtime_rechecks_frozen_safety_configuration(pipeline, tmp_path, tamper):
    task = render_harbor_task(
        pipeline.bundle.public, tmp_path / "tasks", pipeline.request.limits
    )
    plan = build_job_plan(
        pipeline.request,
        jobs_dir=tmp_path / "jobs",
        task_dirs={pipeline.bundle.public.instance_id: task},
        network_hosts=("allowed.agentexam.test",),
    )
    if tamper == "baseline":
        path = task / "task.toml"
        path.write_text(
            path.read_text().replace(
                'network_mode = "allowlist"', 'network_mode = "public"'
            )
        )
    elif tamper == "phase":
        path = task / "task.toml"
        path.write_text(
            path.read_text().replace("[agent]", '[agent]\nnetwork_mode = "public"')
        )
    elif tamper == "compose":
        path = task / "environment/docker-compose.yaml"
        value = json.loads(path.read_text())
        value["services"]["main"]["network_mode"] = "host"
        path.write_text(json.dumps(value))
    elif tamper == "extra":
        plan.config["environment"]["extra_docker_compose"] = ["untrusted.yaml"]
    if tamper is None:
        validate_network_config(plan.config)
    else:
        with pytest.raises(ValueError, match="HARBOR_NETWORK"):
            validate_network_config(plan.config)
