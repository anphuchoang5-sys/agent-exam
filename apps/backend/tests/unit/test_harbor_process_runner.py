from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

import pytest

import eval_platform.adapters.execution.harbor.process_runner as runner_module
from eval_platform.adapters.execution.harbor.process_evidence import (
    LogCaptureSession,
)
from eval_platform.adapters.execution.harbor.process_runner import (
    ProcessOutcome,
    run_bounded_process,
)


def _run(
    tmp_path: Path,
    script: str,
    *,
    timeout_sec: float = 5,
    max_log_bytes: int = 1024,
) -> tuple[Path, ProcessOutcome]:
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


def test_log_capture_finish_is_bounded_while_writers_stay_open(
    tmp_path: Path,
) -> None:
    root = tmp_path / "evidence"
    root.mkdir()
    stdout_read, stdout_write = os.pipe()
    stderr_read, stderr_write = os.pipe()
    stdout = os.fdopen(stdout_read, "rb", buffering=0)
    stderr = os.fdopen(stderr_read, "rb", buffering=0)
    session = LogCaptureSession.start(stdout, stderr, root, 4096)
    started = time.monotonic()
    try:
        captured_stdout, captured_stderr, incomplete = session.finish(timeout_sec=0.05)
    finally:
        os.close(stdout_write)
        os.close(stderr_write)
        for thread in session.threads:
            thread.join(timeout=1)
        stdout.close()
        stderr.close()

    assert time.monotonic() - started < 1
    assert incomplete == ("stdout", "stderr")
    assert captured_stdout.path == (root / "harbor.stdout.log").resolve()
    assert captured_stderr.path == (root / "harbor.stderr.log").resolve()


def test_runner_marks_log_incomplete_when_descendant_keeps_pipe_open(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    evidence_root = tmp_path / "evidence"
    evidence_root.mkdir()
    child_pid_path = tmp_path / "child.pid"

    def terminate_parent_only(process: subprocess.Popen[bytes]) -> tuple[str, ...]:
        process.kill()
        process.wait(timeout=1)
        return ("HARBOR_PROCESS_TREE_CLEANUP_FAILED",)

    monkeypatch.setattr(runner_module, "_terminate_process_tree", terminate_parent_only)
    script = (
        "import pathlib,subprocess,sys,time; "
        "child=subprocess.Popen([sys.executable,'-c','import time;time.sleep(60)']); "
        "pathlib.Path(sys.argv[1]).write_text(str(child.pid)); "
        "print('ready',flush=True);time.sleep(60)"
    )
    started = time.monotonic()
    try:
        outcome = run_bounded_process(
            [sys.executable, "-c", script, str(child_pid_path)],
            cwd=tmp_path,
            env=os.environ.copy(),
            timeout_sec=0.2,
            evidence_root=evidence_root,
            max_log_bytes=4096,
        )
    finally:
        if child_pid_path.is_file():
            try:
                os.kill(int(child_pid_path.read_text()), signal.SIGTERM)
            except ProcessLookupError:
                pass

    assert time.monotonic() - started < 8
    assert outcome.warnings == (
        "HARBOR_PROCESS_TIMEOUT",
        "HARBOR_PROCESS_TREE_CLEANUP_FAILED",
        "HARBOR_LOG_CAPTURE_INCOMPLETE",
    )
