"""Recover Codex trajectories lost to delayed Windows bind-mount visibility."""

from __future__ import annotations

import os
import subprocess
import time
from collections.abc import Callable
from pathlib import Path

from eval_platform.adapters.execution.harbor_entry import harbor_environment

RECOVERY_FAILED = "HARBOR_TRAJECTORY_RECOVERY_FAILED"
_RECOVERY_SCRIPT = """
import sys
from pathlib import Path
from harbor.agents.installed.codex import Codex
from harbor.utils.trajectory_utils import format_trajectory_json

root = Path(sys.argv[1])
agent = Codex(logs_dir=root, config={})
session = agent._get_session_dir()
trajectory = agent._convert_events_to_trajectory(session) if session else None
if trajectory is None:
    raise SystemExit(2)
(root / "trajectory.json").write_text(
    format_trajectory_json(trajectory.to_json_dict()), encoding="utf-8", newline="\\n"
)
""".strip()


def recover_missing_codex_trajectories(
    harbor_executable: Path,
    job_dir: Path,
    *,
    run_process: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
    timeout_sec: float = 2.0,
    pause: Callable[[float], None] = time.sleep,
) -> tuple[str, ...]:
    """Use pinned Harbor's converter once session files become stably readable."""

    missing = tuple(
        agent
        for agent in sorted(job_dir.glob("*/agent"))
        if not _os_path(agent / "trajectory.json").is_file()
        and _os_path(agent / "sessions").is_dir()
    )
    if not missing:
        return ()
    python = harbor_executable.with_name(
        "python.exe" if harbor_executable.suffix == ".exe" else "python"
    )
    if not python.is_file() or python.is_symlink():
        return (RECOVERY_FAILED,)
    failed = False
    for agent_dir in missing:
        target = _os_path(agent_dir / "trajectory.json")
        if target.is_symlink() or not _sessions_stable(
            agent_dir, timeout_sec=timeout_sec, pause=pause
        ):
            failed = True
            continue
        try:
            completed = run_process(
                [
                    str(python.resolve()),
                    "-c",
                    _RECOVERY_SCRIPT,
                    _child_path(agent_dir),
                ],
                cwd=harbor_executable.resolve().parents[2],
                env=harbor_environment(),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=30,
                check=False,
            )
        except (OSError, subprocess.SubprocessError):
            failed = True
            continue
        if completed.returncode != 0 or not target.is_file() or target.is_symlink():
            failed = True
    return (RECOVERY_FAILED,) if failed else ()


def _child_path(path: Path, *, platform: str = os.name) -> str:
    value = str(path.resolve())
    prefix = "\\\\?\\"
    if platform == "nt" and not value.startswith(prefix):
        return prefix + value
    return value


def _os_path(path: Path) -> Path:
    return Path(_child_path(path))


def _sessions_stable(
    agent_dir: Path,
    *,
    timeout_sec: float,
    pause: Callable[[float], None],
) -> bool:
    deadline = time.monotonic() + timeout_sec
    previous: tuple[tuple[str, int, int], ...] | None = None
    while time.monotonic() <= deadline:
        current = _readable_snapshot(agent_dir)
        if current and current == previous:
            return True
        previous = current
        pause(0.05)
    return False


def _readable_snapshot(agent_dir: Path) -> tuple[tuple[str, int, int], ...]:
    snapshot: list[tuple[str, int, int]] = []
    try:
        paths = sorted(_os_path(agent_dir / "sessions").rglob("*.jsonl"))
        for path in paths:
            if path.is_symlink() or not path.is_file():
                return ()
            with path.open("rb") as source:
                if not source.read(1):
                    return ()
            stat = path.stat()
            snapshot.append((str(path.resolve()), stat.st_size, stat.st_mtime_ns))
    except OSError:
        return ()
    return tuple(snapshot)
