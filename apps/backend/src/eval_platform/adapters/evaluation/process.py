from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

from eval_platform.adapters.evaluation.result_mapper import artifact
from eval_platform.adapters.execution.harbor.process_runner import run_bounded_process
from eval_platform.application.ports.evaluator import EvaluationError


def linux_path(path: Path) -> str:
    absolute = path.absolute()
    if os.name != "nt":
        return str(absolute)
    drive = absolute.drive
    if len(drive) != 2 or drive[1] != ":":
        raise ValueError("WSL requires a local drive path")
    return f"/mnt/{drive[0].lower()}/" + "/".join(absolute.parts[1:])


def fork_command(
    repo: Path, directory: Path, arguments: list[str], timeout_sec: int, distro: str
) -> list[str]:
    fork = repo / "framework/swe-bench-fork"
    entry = repo / "apps/backend/src/eval_platform/adapters/evaluation/fork_entry.py"
    # The Linux deadline also kills descendants if the Windows WSL client exits.
    command = [
        "env",
        "-i",
        "PATH=/usr/bin:/bin",
        "LANG=C.UTF-8",
        f"HOME={linux_path(directory / 'home')}",
        "PYTHONUTF8=1",
        f"PYTHONPYCACHEPREFIX={linux_path(repo / 'runtime/cache/fork-pycache')}",
        "PYTHON_DOTENV_DISABLED=1",
        "HF_HUB_OFFLINE=1",
        "HF_DATASETS_OFFLINE=1",
        f"PYTHONPATH={linux_path(fork)}",
        "timeout",
        "--signal=TERM",
        "--kill-after=10s",
        str(timeout_sec),
        linux_path(fork / ".venv/bin/python"),
        linux_path(entry),
        linux_path(directory / "profile.json"),
        *arguments,
    ]
    if os.name == "nt":
        return ["wsl", "-d", distro, "--cd", linux_path(directory), "--", *command]
    return command


def execute_fork(
    command: list[str],
    directory: Path,
    timeout_sec: int,
    run_id: str,
    *,
    artifact_root: Path,
) -> None:
    # Reuse the existing tested byte-bounded process capture; no new transport.
    try:
        outcome = run_bounded_process(
            command,
            cwd=directory,
            env=os.environ,
            timeout_sec=timeout_sec + 30,
            evidence_root=directory,
        )
    finally:
        cleanup_ok = cleanup_run(run_id, directory)
    for stream in ("stdout", "stderr"):
        (directory / f"harbor.{stream}.log").rename(directory / f"fork.{stream}.log")
    manifest_path = directory / "harbor-process.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    for stream in ("stdout", "stderr"):
        manifest["logs"][stream]["file"] = f"fork.{stream}.log"
    manifest["warnings"] = [
        item.replace("HARBOR_", "HARNESS_") for item in outcome.warnings
    ]
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    manifest_path.rename(directory / "fork-process.json")
    refs = tuple(
        artifact(directory / name, artifact_root, "harness_process")
        for name in (
            "fork-process.json",
            "fork.stdout.log",
            "fork.stderr.log",
            "cleanup.json",
        )
    )
    if not cleanup_ok:
        raise EvaluationError(
            "HARNESS_CLEANUP_FAILED", "Evaluator container cleanup failed", refs
        )
    if outcome.start_error or outcome.returncode != 0 or outcome.timed_out:
        raise EvaluationError(
            "HARNESS_PROCESS_FAILED", "Fixed Fork process did not complete", refs
        )
    if outcome.warnings:
        raise EvaluationError(
            "HARNESS_LOG_INCOMPLETE", "Evaluator process evidence is incomplete", refs
        )


def cleanup_run(run_id: str, directory: Path) -> bool:
    label = f"agentexam.evaluator.run={run_id}"
    profile = json.loads((directory / "profile.json").read_text(encoding="utf-8"))
    ownership = f"agentexam.evaluator.evidence={profile['evidence_identity']}"
    record: dict[str, object] = {
        "label": label,
        "ownership": ownership,
        "removed_ids": [],
        "remaining_ids": [],
    }
    try:

        def query() -> list[str]:
            result = subprocess.run(
                [
                    "docker",
                    "ps",
                    "-aq",
                    "--filter",
                    f"label={label}",
                    "--filter",
                    f"label={ownership}",
                ],
                check=True,
                capture_output=True,
                text=True,
                timeout=30,
            )
            return result.stdout.split()

        remaining = query()
        for container_id in remaining:
            subprocess.run(
                ["docker", "rm", "-f", container_id],
                check=True,
                capture_output=True,
                timeout=30,
            )
        record["removed_ids"] = remaining
        record["remaining_ids"] = query()
        record["verified"] = not record["remaining_ids"]
    except (OSError, subprocess.SubprocessError):
        record["verified"] = False
    (directory / "cleanup.json").write_text(
        json.dumps(record, indent=2), encoding="utf-8"
    )
    return record["verified"] is True
