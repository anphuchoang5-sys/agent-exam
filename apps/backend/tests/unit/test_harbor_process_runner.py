from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

from eval_platform.adapters.execution.harbor.process_runner import (
    run_bounded_process,
)


def _run(
    tmp_path: Path,
    script: str,
    *,
    timeout_sec: float = 5,
    max_log_bytes: int = 1024,
):
    evidence_root = tmp_path / "evidence"
    evidence_root.mkdir()
    outcome = run_bounded_process(
        [sys.executable, "-c", script],
        cwd=tmp_path,
        env=os.environ.copy(),
        timeout_sec=timeout_sec,
        evidence_root=evidence_root,
        max_log_bytes=max_log_bytes,
    )
    return evidence_root, outcome


def test_streams_both_logs_to_hard_limit_and_marks_truncation(tmp_path: Path) -> None:
    root, outcome = _run(
        tmp_path,
        "import sys; sys.stdout.buffer.write(b'abcdefgh'); "
        "sys.stderr.buffer.write(b'12345678')",
        max_log_bytes=5,
    )

    assert outcome.returncode == 0 and not outcome.timed_out
    assert outcome.warnings == (
        "HARBOR_STDOUT_TRUNCATED",
        "HARBOR_STDERR_TRUNCATED",
    )
    assert (root / "harbor.stdout.log").read_bytes() == b"abcde"
    assert (root / "harbor.stderr.log").read_bytes() == b"12345"
    manifest = json.loads((root / "harbor-process.json").read_text("utf-8"))
    assert manifest["logs"]["stdout"] == {
        "file": "harbor.stdout.log",
        "max_bytes": 5,
        "saved_bytes": 5,
        "truncated": True,
    }
    assert manifest["logs"]["stderr"]["truncated"] is True


def test_timeout_terminates_process_and_preserves_partial_log(tmp_path: Path) -> None:
    started = time.monotonic()
    root, outcome = _run(
        tmp_path,
        "import time; print('ready', flush=True); time.sleep(60)",
        timeout_sec=0.5,
    )

    assert time.monotonic() - started < 10
    assert outcome.returncode == 124 and outcome.timed_out
    assert outcome.warnings[0] == "HARBOR_PROCESS_TIMEOUT"
    assert set(outcome.warnings) <= {
        "HARBOR_PROCESS_TIMEOUT",
        "HARBOR_PROCESS_TREE_CLEANUP_FAILED",
    }
    assert (root / "harbor.stdout.log").read_text("utf-8") == "ready\n"
    manifest = json.loads((root / "harbor-process.json").read_text("utf-8"))
    assert manifest["timed_out"] is True


def test_start_failure_is_structured_and_bounded(tmp_path: Path) -> None:
    root = tmp_path / "evidence"
    root.mkdir()
    outcome = run_bounded_process(
        [str(tmp_path / "missing-harbor.exe")],
        cwd=tmp_path,
        env=os.environ.copy(),
        timeout_sec=1,
        evidence_root=root,
        max_log_bytes=4096,
    )

    assert isinstance(outcome.start_error, FileNotFoundError)
    assert outcome.returncode == -1 and not outcome.timed_out
    assert outcome.warnings == ("HARBOR_PROCESS_START_FAILED",)
    assert (root / "harbor.stdout.log").read_bytes() == b""
    manifest = json.loads((root / "harbor-process.json").read_text("utf-8"))
    assert manifest["start_error_type"] == "FileNotFoundError"
