"""Internal Harbor network assets; no public policy API or implicit egress."""

from __future__ import annotations

import hashlib
import ipaddress
import json
import re
import subprocess
from pathlib import Path
from typing import Any

from eval_platform.application.ports.execution import RunLimits

SIDECAR = "harbor-docker-egress-control-sidecar"
_HOST = re.compile(
    r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?(?:\.[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?)+"
)
_SOURCE_FILES = (
    "Dockerfile",
    "entrypoint.sh",
    "gost.yaml",
    "allowlist.txt",
    "bin/network-policy",
)
_DNS_GUARD = b"""\
  # AgentExam: support only the owner-approved Docker Desktop DNS profile.
  dns_config="$(awk '
    /^[[:space:]]*nameserver[[:space:]]/ || /^# ExtServers:/ { print }
  ' /etc/resolv.conf)"
  if [ "$dns_config" != 'nameserver 127.0.0.11
# ExtServers: [192.168.65.7]' ]; then
    echo HARBOR_DOCKER_DNS_CONFIG_UNSUPPORTED >&2
    exit 1
  fi
"""


def validate_hosts(hosts: tuple[str, ...]) -> tuple[str, ...]:
    """Accept exact DNS names from trusted local composition, not user URLs."""
    if not isinstance(hosts, tuple):
        raise ValueError("Registered hosts must be an immutable tuple")
    result = set()
    for item in hosts:
        if not isinstance(item, str):
            raise ValueError("Registered host must be a DNS name")
        host = item.lower()
        if (
            len(host) > 253
            or not _HOST.fullmatch(host)
            or host.endswith((".internal", ".local", ".localhost", ".home.arpa"))
        ):
            raise ValueError("Only exact registered external DNS names are allowed")
        try:
            ipaddress.ip_address(host)
        except ValueError:
            result.add(host)
        else:
            raise ValueError("IP allowlists are not registered for M0")
    return tuple(sorted(result))


def compose_profile(limits: RunLimits) -> dict[str, Any]:
    """M0 caps; deliberately omit networking so Harbor attaches its sidecar."""
    common = {
        "cap_drop": ["ALL"],
        "security_opt": ["no-new-privileges:true"],
        "pids_limit": 64,
    }
    main = {
        **common,
        "cpus": limits.cpus,
        "mem_limit": f"{limits.memory_mb}m",
        "memswap_limit": f"{limits.memory_mb}m",
        "environment": {
            **{
                key: ""
                for key in (
                    "HTTP_PROXY",
                    "HTTPS_PROXY",
                    "ALL_PROXY",
                    "http_proxy",
                    "https_proxy",
                    "all_proxy",
                )
            },
            "NO_PROXY": "*",
            "no_proxy": "*",
        },
    }
    sidecar = {**common, "cpus": 0.5, "mem_limit": "128m", "memswap_limit": "128m"}
    return {"services": {"main": main, SIDECAR: sidecar}}


def _adapt_dns_policy(data: bytes) -> bytes:
    """Patch only fixed anchors; unknown upstream layouts cannot start a trial."""
    changes = {
        b"setup_nftables() {\n": _DNS_GUARD,
        b"$(nft_dns_rules accept)\n": (
            b"    ip daddr 192.168.65.7 udp dport 53 accept\n"
        ),
    }
    for anchor, addition in changes.items():
        if data.count(anchor) != 1:
            raise ValueError("HARBOR_DNS_POLICY_SOURCE_UNSUPPORTED")
        data = data.replace(anchor, anchor + addition, 1)
    return data


def export_sidecar(harbor_root: Path, destination: Path, revision: str) -> None:
    """Export fixed blobs plus the approved DNS adaptation, recording both IDs."""

    def git(*args: str) -> bytes:
        return subprocess.run(
            ["git", "-C", str(harbor_root), *args],
            check=True,
            capture_output=True,
            timeout=10,
        ).stdout

    if (
        git("rev-parse", "HEAD").decode().strip() != revision
        or git("status", "--porcelain", "--untracked-files=no").strip()
    ):
        raise ValueError("HARBOR_SOURCE_NOT_FIXED")
    destination.mkdir(parents=True, exist_ok=False)
    hashes = {}
    upstream_hashes = {}
    for name in _SOURCE_FILES:
        data = git(
            "show", f"{revision}:src/harbor/environments/docker/{SIDECAR}/{name}"
        )
        upstream_hashes[name] = hashlib.sha256(data).hexdigest()
        if name == "bin/network-policy":
            data = _adapt_dns_policy(data)
        target = destination / name
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("xb") as stream:
            stream.write(data)
        hashes[name] = hashlib.sha256(data).hexdigest()
    with (destination.parent / "network-source.json").open(
        "x", encoding="utf-8"
    ) as manifest_stream:
        json.dump(
            {
                "revision": revision,
                "upstream_sha256": upstream_hashes,
                "sha256": hashes,
                "adaptation": "docker-desktop-dns-192.168.65.7-udp53-v1",
            },
            manifest_stream,
            indent=2,
        )
