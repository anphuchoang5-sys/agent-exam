"""Five fail-closed S11 verdict groups over captured Docker evidence."""

from __future__ import annotations

from pathlib import Path
from typing import Any

SIDECAR = "harbor-docker-egress-control-sidecar"
SERVICES = ("main", "proxy", "fake-upstream", SIDECAR)


def verify(snapshot: dict[str, Any]) -> dict[str, list[str]]:
    return {
        "topology": _topology(snapshot),
        "direct_refusal": _direct(snapshot),
        "host_isolation": _host(snapshot),
        "fake_key": _secret(snapshot),
        "precise_cleanup": _cleanup(snapshot),
    }


def require_verified(snapshot: dict[str, Any]) -> None:
    failed = {name: items for name, items in verify(snapshot).items() if items}
    if failed:
        raise AssertionError(f"S11_ASSERTIONS_FAILED:{failed}")


def _scopes(snapshot: dict[str, Any]) -> tuple[str, ...]:
    return tuple(snapshot.get("scopes", ()))


def _containers(snapshot: dict[str, Any], scope: str) -> dict[str, dict[str, Any]]:
    result = {}
    for item in snapshot.get("containers", ()):
        labels = item.get("Config", {}).get("Labels", {})
        if labels.get("agentexam.scope") == scope:
            result[labels.get("com.docker.compose.service", "")] = item
    return result


def _network_roles(snapshot: dict[str, Any], scope: str) -> dict[str, str]:
    result = {}
    for item in snapshot.get("networks", ()):
        labels = item.get("Labels", {})
        if labels.get("agentexam.scope") == scope:
            result[item.get("Id", "")] = labels.get("com.docker.compose.network", "")
    return result


def _roles(container: dict[str, Any], roles: dict[str, str]) -> set[str]:
    return {
        roles.get(value.get("NetworkID", ""), "")
        for value in container.get("NetworkSettings", {}).get("Networks", {}).values()
    } - {""}


def _topology(snapshot: dict[str, Any]) -> list[str]:
    failures = []
    expected = {
        "main": {"internal"},
        "proxy": {"internal", "egress"},
        "fake-upstream": {"egress"},
        SIDECAR: {"egress"},
    }
    seen_network_ids = []
    for scope in _scopes(snapshot):
        containers, roles = (
            _containers(snapshot, scope),
            _network_roles(snapshot, scope),
        )
        if set(containers) != set(SERVICES):
            failures.append(f"{scope}:services={sorted(containers)}")
        for service, wanted in expected.items():
            if service in containers and _roles(containers[service], roles) != wanted:
                failures.append(f"{scope}:{service}-networks")
        owned = [
            item
            for item in snapshot.get("networks", ())
            if item.get("Labels", {}).get("agentexam.scope") == scope
        ]
        internal = {
            item.get("Labels", {}).get("com.docker.compose.network"): item.get(
                "Internal"
            )
            for item in owned
        }
        if internal != {"internal": True, "egress": False}:
            failures.append(f"{scope}:network-internal={internal}")
        seen_network_ids.append(frozenset(item.get("Id") for item in owned))
    if len(seen_network_ids) == 2 and seen_network_ids[0] & seen_network_ids[1]:
        failures.append("trials-share-network")
    return failures


def _direct(snapshot: dict[str, Any]) -> list[str]:
    expected = {
        "own_proxy": "OPEN",
        "own_upstream": "CLOSED",
        "public": "CLOSED",
        "host_gateway": "CLOSED",
        "metadata": "CLOSED",
        "other_trial": "CLOSED",
        "proxy_upstream": "RECORDED",
    }
    failures = []
    for scope in _scopes(snapshot):
        readings = snapshot.get("readings", {}).get(scope, {})
        for name, wanted in expected.items():
            if readings.get(name) != wanted:
                failures.append(f"{scope}:{name}={readings.get(name)}")
    return failures


def _host(snapshot: dict[str, Any]) -> list[str]:
    failures = []
    allowed_root = Path(snapshot.get("allowed_mount_root", ".")).resolve()
    for scope in _scopes(snapshot):
        for service, item in _containers(snapshot, scope).items():
            bindings = item.get("HostConfig", {}).get("PortBindings")
            if bindings not in (None, {}):
                failures.append(f"{scope}:{service}:published-port")
            mounts = item.get("Mounts", ())
            if service != "main" and mounts:
                failures.append(f"{scope}:{service}:mount")
            for mount in mounts if service == "main" else ():
                source = Path(mount.get("Source", "")).resolve()
                destination = mount.get("Destination", "")
                if allowed_root not in source.parents or destination not in {
                    "/logs/agent",
                    "/logs/artifacts",
                    "/logs/verifier",
                }:
                    failures.append(f"{scope}:main:unexpected-mount")
            if any("docker.sock" in str(mount) for mount in mounts):
                failures.append(f"{scope}:{service}:docker-socket")
    return failures


def _secret(snapshot: dict[str, Any]) -> list[str]:
    failures = []
    for scope in _scopes(snapshot):
        values = snapshot.get("secret", {}).get(scope, {})
        if values.get("proxy_private_control") != 1:
            failures.append(f"{scope}:private-positive-control")
        for name in (
            "workload_file_hits",
            "workload_environ_hits",
            "workload_argv_hits",
        ):
            if values.get(name) != 0:
                failures.append(f"{scope}:{name}={values.get(name)}")
    if snapshot.get("public_secret_hits") != 0:
        failures.append("public-output-secret-hit")
    return failures


def _cleanup(snapshot: dict[str, Any]) -> list[str]:
    residual = snapshot.get("residual", {})
    return [f"{kind}={values}" for kind, values in residual.items() if values]
