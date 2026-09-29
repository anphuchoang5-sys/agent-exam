from __future__ import annotations

import json
import subprocess
from copy import deepcopy

import pytest
from providers.runtime.s11.docker_io import DockerIO
from providers.runtime.s11.verdicts import require_verified, verify
from providers.runtime.s11.verify import _inventory_identities


def _network(scope: str, role: str, identity: str, internal: bool):
    return {
        "Id": identity,
        "Internal": internal,
        "Labels": {
            "agentexam.task": "05",
            "agentexam.scope": scope,
            "com.docker.compose.network": role,
        },
    }


def _container(scope: str, service: str, network_ids: dict[str, str]):
    networks = {name: {"NetworkID": identity} for name, identity in network_ids.items()}
    mounts = []
    if service == "main":
        mounts = [
            {"Source": f"C:/evidence/{scope}/{name}", "Destination": f"/logs/{name}"}
            for name in ("agent", "artifacts", "verifier")
        ]
    return {
        "Config": {
            "Labels": {"agentexam.scope": scope, "com.docker.compose.service": service}
        },
        "HostConfig": {"PortBindings": {}},
        "Mounts": mounts,
        "NetworkSettings": {"Networks": networks},
    }


def snapshot():
    scopes = ("t05-s11-one", "t05-s11-two")
    result = {
        "scopes": scopes,
        "allowed_mount_root": "C:/evidence",
        "containers": [],
        "networks": [],
        "readings": {},
        "secret": {},
        "public_secret_hits": 0,
        "residual": {"containers": [], "networks": [], "volumes": []},
    }
    for index, scope in enumerate(scopes):
        ids = {"internal": f"i{index}", "egress": f"e{index}"}
        result["networks"] += [
            _network(scope, "internal", ids["internal"], True),
            _network(scope, "egress", ids["egress"], False),
        ]
        assignments = {
            "main": {"internal": ids["internal"]},
            "proxy": ids,
            "fake-upstream": {"egress": ids["egress"]},
            "harbor-docker-egress-control-sidecar": {"egress": ids["egress"]},
        }
        result["containers"] += [
            _container(scope, service, networks)
            for service, networks in assignments.items()
        ]
        result["readings"][scope] = {
            "own_proxy": "OPEN",
            "own_upstream": "CLOSED",
            "public": "CLOSED",
            "host_gateway": "CLOSED",
            "metadata": "CLOSED",
            "other_trial": "CLOSED",
            "proxy_upstream": "RECORDED",
        }
        result["secret"][scope] = {
            "proxy_private_control": 1,
            "workload_file_hits": 0,
            "workload_environ_hits": 0,
            "workload_argv_hits": 0,
        }
    return result


def test_all_five_groups_accept_the_verified_shape():
    evidence = snapshot()
    require_verified(evidence)
    assert verify(evidence) == {name: [] for name in verify(evidence)}


@pytest.mark.parametrize(
    "group",
    ["topology", "direct_refusal", "host_isolation", "fake_key", "precise_cleanup"],
)
def test_each_group_has_a_distinguishing_negative_control(group):
    evidence = deepcopy(snapshot())
    if group == "topology":
        evidence["containers"][0]["NetworkSettings"]["Networks"]["egress"] = {
            "NetworkID": "e0"
        }
    elif group == "direct_refusal":
        evidence["readings"]["t05-s11-one"]["metadata"] = "OPEN"
    elif group == "host_isolation":
        evidence["containers"][0]["HostConfig"]["PortBindings"] = {
            "80/tcp": [{"HostPort": "80"}]
        }
    elif group == "fake_key":
        evidence["secret"]["t05-s11-one"]["workload_file_hits"] = 1
    else:
        evidence["residual"]["containers"] = ["left-behind"]
    assert verify(evidence)[group]
    with pytest.raises(AssertionError, match="S11_ASSERTIONS_FAILED"):
        require_verified(evidence)
    require_verified(snapshot())


def test_docker_stdin_keeps_linux_line_endings(tmp_path, monkeypatch) -> None:
    captured = {}

    def run(command, **kwargs):
        captured.update(kwargs)
        return subprocess.CompletedProcess(command, 0, b"ok\n", b"")

    monkeypatch.setattr(subprocess, "run", run)
    docker = DockerIO(tmp_path)
    try:
        result = docker.run("docker", "exec", "probe", stdin="one\ntwo\n")
    finally:
        docker.close()

    assert captured["input"] == b"one\ntwo\n"
    assert result.stdout == "ok\n"


def test_image_inventory_ignores_relative_age(tmp_path) -> None:
    first = tmp_path / "first.jsonl"
    second = tmp_path / "second.jsonl"
    base = {"ID": "sha256:one", "Repository": "probe", "Tag": "one", "Digest": ""}
    first.write_text(json.dumps({**base, "CreatedSince": "one minute ago"}) + "\n")
    second.write_text(json.dumps({**base, "CreatedSince": "two minutes ago"}) + "\n")

    assert _inventory_identities(first, "images") == _inventory_identities(
        second, "images"
    )
