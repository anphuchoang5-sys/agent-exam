"""Produce only the T2-proven dual-network shape for a controlled fake Run.

This document is an internal overlay, not a caller-defined Compose extension.
The product entry must revalidate it before passing it to fixed Harbor.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from eval_platform.adapters.execution.network import SIDECAR

_SCOPE = re.compile(r"t05-[a-z0-9-]{3,59}")
_IMAGE = re.compile(r"sha256:[0-9a-f]{64}")


def compose_overlay(
    *, scope: str, proxy_image: str, upstream_image: str
) -> dict[str, Any]:
    """Make an immutable-in-shape candidate; only vetted image IDs vary."""
    if not _SCOPE.fullmatch(scope) or not all(
        _IMAGE.fullmatch(image) for image in (proxy_image, upstream_image)
    ):
        raise ValueError("PROVIDER_TOPOLOGY_INVALID")
    labels = {"agentexam.task": "05", "agentexam.scope": scope}
    common = {
        "labels": labels,
        "cap_drop": ["ALL"],
        "security_opt": ["no-new-privileges:true"],
        "pids_limit": 64,
        "read_only": True,
        "tmpfs": ["/tmp:rw,nosuid,nodev,size=64m,uid=65534,gid=65534"],
        "user": "65534:65534",
    }
    return {
        "services": {
            "main": {
                "labels": labels,
                "networks": ["internal"],
                "depends_on": {"proxy": {"condition": "service_healthy"}},
            },
            "proxy": {
                **common,
                "image": proxy_image,
                "command": ["proxy"],
                "environment": {"AGENTEXAM_RUN_ID": scope},
                "networks": ["internal", "egress"],
                "healthcheck": {
                    "test": [
                        "CMD",
                        "python",
                        "-c",
                        "import socket; "
                        "[socket.create_connection(target,2).close() for target in "
                        "(('127.0.0.1',8080),('fake-upstream.t05.invalid',443))]",
                    ],
                    "interval": "2s",
                    "timeout": "3s",
                    "retries": 10,
                },
            },
            "fake-upstream": {
                **common,
                "image": upstream_image,
                "command": ["fake-upstream"],
                "networks": {"egress": {"aliases": ["fake-upstream.t05.invalid"]}},
            },
            SIDECAR: {"labels": labels, "networks": ["egress"]},
        },
        "networks": {
            "internal": {"internal": True, "labels": labels},
            "egress": {"internal": False, "labels": labels},
        },
    }


def validate_overlay(
    document: Any, *, scope: str, proxy_image: str, upstream_image: str
) -> None:
    """Reject every unexpected service, network, mount, port, or override."""
    if document != compose_overlay(
        scope=scope, proxy_image=proxy_image, upstream_image=upstream_image
    ):
        raise ValueError("PROVIDER_TOPOLOGY_INVALID")


def validate_compose_file(
    path: Path,
    configured_paths: object,
    *,
    scope: str,
    proxy_image: str,
    upstream_image: str,
) -> None:
    """Product-entry guard for the one internally generated Compose overlay."""
    if (
        path.name != "provider-compose.json"
        or path.is_symlink()
        or configured_paths != [str(path.resolve())]
    ):
        raise ValueError("HARBOR_NETWORK_CONFIG_INVALID")
    try:
        if path.stat().st_size > 65536:
            raise ValueError
        document = json.loads(path.read_text(encoding="utf-8"))
        validate_overlay(
            document,
            scope=scope,
            proxy_image=proxy_image,
            upstream_image=upstream_image,
        )
    except (OSError, UnicodeError, ValueError):
        raise ValueError("HARBOR_NETWORK_CONFIG_INVALID") from None
