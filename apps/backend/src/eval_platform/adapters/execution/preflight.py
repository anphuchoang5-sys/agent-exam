"""No-model diagnostics for the existing execution backend, never acceptance."""

from __future__ import annotations

import json
import re
import subprocess
import uuid
from pathlib import Path

from eval_platform.adapters.tasks.swe_gym import (
    CANDIDATE_IMAGE,
    CANDIDATE_INSTANCE_ID,
    DATASET_REVISION,
    SWEGymTaskSource,
)

_SCRIPT = """set -o pipefail
printf 'KERNEL=%s\\n' "$(uname -r)"
if [ ! -r /proc/config.gz ]; then
    echo NFT_FIB_INET=unknown
    exit 0
fi
zcat /proc/config.gz | awk '
    /^CONFIG_NFT_FIB_INET=[ym]$/ { found=1 }
    END { print "NFT_FIB_INET=" (found ? "supported" : "unsupported") }
'
"""


def task_preflight(repo: Path) -> dict[str, object]:
    source = SWEGymTaskSource(
        repo / "runtime/cache/swe-gym-lite" / DATASET_REVISION / "train-0000.parquet"
    )
    bundle = source.load(CANDIDATE_INSTANCE_ID)
    return {
        "prototype": True,
        "task_snapshot_verified": True,
        "instance_id": bundle.public.instance_id,
        "real_codex_ready": False,
        "pending": [
            "fixed Codex version/model/effort",
            "network allowlist",
            "secret lifecycle",
        ],
    }


def network_preflight(directory: Path) -> dict[str, object]:
    """Inspect daemon kernel in a pinned, offline, short-lived container."""
    directory.mkdir(parents=True, exist_ok=False)
    identity = f"agentexam-network-{uuid.uuid4().hex[:12]}"
    label = f"agentexam.network.preflight={identity}"
    command = [
        "docker",
        "run",
        "--rm",
        "--pull=never",
        "--name",
        identity,
        "--label",
        label,
        "--network",
        "none",
        "--read-only",
        "--cap-drop",
        "ALL",
        "--security-opt",
        "no-new-privileges",
        "--cpus",
        "1",
        "--memory",
        "64m",
        "--memory-swap",
        "64m",
        "--pids-limit",
        "32",
        CANDIDATE_IMAGE,
        "bash",
        "-lc",
        _SCRIPT,
    ]
    record: dict[str, object] = {
        "schema_version": 1,
        "prototype": True,
        "real_codex_ready": False,
        "status": "PROBE_INCOMPLETE",
        "kernel_supported": None,
        "probe_id": identity,
        "image": CANDIDATE_IMAGE,
        "argv": command,
    }
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=30,
            check=False,
        )
        record["returncode"] = result.returncode
        if result.returncode == 0:
            record.update(_parse(result.stdout))
        else:
            record["status"] = "PROBE_PROCESS_FAILED"
    except FileNotFoundError:
        record["status"] = "DOCKER_UNAVAILABLE"
    except (OSError, subprocess.SubprocessError):
        record["status"] = "PROBE_PROCESS_FAILED"
    finally:
        record["probe_status"] = record["status"]
        cleanup = _cleanup(identity, label)
        record["cleanup"] = cleanup
        if not cleanup["verified"]:
            record["status"] = "PROBE_CLEANUP_UNVERIFIED"
        with (directory / "network-preflight.json").open(
            "x", encoding="utf-8"
        ) as stream:
            json.dump(record, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
    return record


def _parse(output: str) -> dict[str, object]:
    # Persist only the expected protocol; arbitrary stderr/exception text may leak.
    match = re.fullmatch(
        r"KERNEL=([A-Za-z0-9_.+-]{1,128})\r?\n"
        r"NFT_FIB_INET=(supported|unsupported|unknown)\r?\n",
        output,
    )
    if match is None:
        return {"status": "PROBE_PROTOCOL_ERROR"}
    kernel, capability = match.groups()
    return {
        "kernel": kernel,
        "kernel_supported": None
        if capability == "unknown"
        else capability == "supported",
        "status": {
            "supported": "SUPPORTED_KERNEL",
            "unsupported": "UNSUPPORTED_KERNEL",
            "unknown": "KERNEL_CAPABILITY_UNKNOWN",
        }[capability],
    }


def _cleanup(identity: str, label: str) -> dict[str, object]:
    record: dict[str, object] = {
        "verified": False,
        "removed_ids": [],
        "remaining_ids": [],
    }

    def query() -> list[str]:
        result = subprocess.run(
            [
                "docker",
                "ps",
                "-aq",
                "--filter",
                f"label={label}",
                "--filter",
                f"name=^/{identity}$",
            ],
            capture_output=True,
            text=True,
            timeout=10,
            check=True,
        )
        identities = result.stdout.split()
        if any(not re.fullmatch(r"[a-f0-9]{12,64}", value) for value in identities):
            raise ValueError("Invalid Docker container identity")
        return identities

    try:
        remaining = query()
        if remaining:
            subprocess.run(
                ["docker", "rm", "-f", *remaining],
                capture_output=True,
                timeout=10,
                check=True,
            )
        record["removed_ids"] = remaining
        record["remaining_ids"] = query()
        record["verified"] = not record["remaining_ids"]
    except (OSError, subprocess.SubprocessError, ValueError):
        pass
    return record
